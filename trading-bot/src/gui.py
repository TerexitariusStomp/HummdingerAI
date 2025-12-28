import logging
from datetime import datetime
from typing import Any, Dict

import streamlit as st
from web3 import HTTPProvider, Web3

from config import Settings, get_settings
from eliza_agent import ElizaTradingAgent
from hummingbot_controller import HummingbotController
from market_data import MarketDataService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@st.cache_resource
def bootstrap(settings: Settings):
    market = MarketDataService(settings.exchange_id, settings.exchange_api_key, settings.exchange_secret)
    agent = ElizaTradingAgent(
        prompt="You are an on-chain trading assistant. Return concise actions: buy/sell/hold.",
    )
    hummingbot = HummingbotController(
        strategy=settings.hummingbot_strategy,
        hummingbot_path=settings.hummingbot_path,
        gateway_url=settings.hummingbot_gateway,
    )
    web3 = Web3(HTTPProvider(settings.rpc_url))
    return market, agent, hummingbot, web3


def fetch_context(market: MarketDataService, symbol: str) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "ohlcv": market.fetch_ohlcv(symbol, timeframe="5m", limit=30),
        "ticker": market.fetch_ticker(symbol),
        "order_book": market.fetch_order_book(symbol),
    }


def render_header(settings: Settings, web3: Web3) -> None:
    st.title(settings.app_title)
    st.caption(f"Network: {settings.network_name}")
    try:
        block_number = web3.eth.block_number
        st.write(f"Latest block: {block_number}")
    except Exception as exc:  # pragma: no cover - guardrail for RPC quirks
        st.warning(f"Could not load block height: {exc}")


def render_market_tables(context: Dict[str, Any]) -> None:
    ticker = context["ticker"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Last Price", f"{ticker['last']:.4f}")
    col2.metric("24h Change", f"{ticker.get('percentage', 0):.2f}%")
    col3.metric("Volume 24h", f"{ticker.get('baseVolume', 0):,.2f}")

    st.subheader("Order Book (Top 10)")
    order_book = context["order_book"]
    st.write(
        {
            "bids": order_book.get("bids", [])[:10],
            "asks": order_book.get("asks", [])[:10],
        }
    )

    st.subheader("Recent OHLCV (5m)")
    ohlcv_rows = [
        {
            "time": datetime.fromtimestamp(row[0] / 1000),
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
        }
        for row in context["ohlcv"]
    ]
    st.dataframe(ohlcv_rows)


def main() -> None:
    st.set_page_config(page_title="ElizaOS Trading Bot", layout="wide")
    try:
        settings = get_settings()
    except Exception as exc:
        st.error(f"Configuration error: {exc}")
        return

    market, agent, hummingbot, web3 = bootstrap(settings)
    render_header(settings, web3)

    symbol = st.sidebar.text_input("Symbol (CCXT format)", "ETH/USDT")
    auto_push = st.sidebar.checkbox("Send signals to Hummingbot", value=False)

    if st.button("Refresh data / generate signal"):
        context = fetch_context(market, symbol)
        render_market_tables(context)
        signal = agent.generate_signal(context)
        st.success(f"Agent signal: {signal}")
        if auto_push:
            hummingbot.send_signal(signal, symbol)
            st.info("Signal forwarded to Hummingbot gateway/client.")

    st.sidebar.markdown("Private keys are read from your .env; Flashbots is wired via backend code.")
    st.sidebar.markdown("Use the headless runner (main.py) for automated loops.")


if __name__ == "__main__":
    main()
