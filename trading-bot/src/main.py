import logging
from typing import Dict

from config import get_settings
from eliza_agent import ElizaTradingAgent
from flashbots_executor import FlashbotsExecutor
from hummingbot_controller import HummingbotController
from market_data import MarketDataService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


DEFAULT_SYMBOL = "ETH/USDT"
PROMPT = "You are an on-chain trading agent. Produce high-confidence, risk-aware trade signals."


def build_market_context(market: MarketDataService, symbol: str) -> Dict:
    ohlcv = market.fetch_ohlcv(symbol, timeframe="5m", limit=60)
    ticker = market.fetch_ticker(symbol)
    order_book = market.fetch_order_book(symbol)
    return {
        "symbol": symbol,
        "ohlcv": ohlcv,
        "ticker": ticker,
        "order_book": order_book,
    }


def main() -> None:
    settings = get_settings()
    market = MarketDataService(settings.exchange_id, settings.exchange_api_key, settings.exchange_secret)
    market_context = build_market_context(market, DEFAULT_SYMBOL)

    agent = ElizaTradingAgent(prompt=PROMPT)
    signal = agent.generate_signal(market_context)
    logger.info("Signal: %s", signal)

    hummingbot = HummingbotController(
        strategy=settings.hummingbot_strategy,
        hummingbot_path=settings.hummingbot_path,
        gateway_url=settings.hummingbot_gateway,
    )
    hummingbot.send_signal(signal, DEFAULT_SYMBOL)

    flashbots_executor = FlashbotsExecutor(
        rpc_url=settings.rpc_url,
        private_key=settings.private_key,
        relay_endpoint=settings.flashbots_relay,
        block_priority_gwei=settings.flashbots_block_priority_gwei,
    )
    flashbots_executor.connect()
    if signal.get("action") != "hold":
        logger.info("Prepare custom token flash-loan bundle here.")
        # Intentionally no default bundle submission to avoid accidental txs.

    market.close()


if __name__ == "__main__":
    main()
