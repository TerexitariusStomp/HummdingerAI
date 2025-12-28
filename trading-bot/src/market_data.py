import logging
from typing import Any, Dict, List, Optional

import ccxt
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class MarketDataService:
    """Lightweight CCXT wrapper to keep agents/GUI fed with market data."""

    def __init__(
        self,
        exchange_id: str,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> None:
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(
            {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
            }
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        logger.debug("Fetching ticker for %s", symbol)
        return self.exchange.fetch_ticker(symbol)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def fetch_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 50) -> List[List[Any]]:
        logger.debug("Fetching OHLCV for %s %s limit=%s", symbol, timeframe, limit)
        return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

    def fetch_order_book(self, symbol: str, depth: int = 10) -> Dict[str, Any]:
        try:
            return self.exchange.fetch_order_book(symbol, limit=depth)
        except ccxt.BaseError as exc:  # pragma: no cover - just safety
            logger.warning("Order book fetch failed for %s: %s", symbol, exc)
            return {"bids": [], "asks": []}

    def close(self) -> None:
        try:
            self.exchange.close()
        except Exception:  # pragma: no cover - best effort cleanup
            pass
