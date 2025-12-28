import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:  # Lazy import to keep the project runnable without ElizaOS installed.
    from eliza import Agent  # type: ignore
except ImportError:
    Agent = None


class ElizaTradingAgent:
    """Adapter around ElizaOS agent for signal generation."""

    def __init__(self, prompt: str, tools: Optional[List[Any]] = None) -> None:
        self.prompt = prompt
        self.tools = tools or []
        self.agent = None

        if Agent is None:
            logger.warning(
                "ElizaOS not installed. Falling back to heuristic signals. "
                "Install the ElizaOS package and restart."
            )
        else:
            # The Agent signature depends on ElizaOS version; adjust as needed.
            self.agent = Agent(system_prompt=prompt, tools=self.tools)

    def _fallback_signal(self, ohlcv: List[List[Any]]) -> Dict[str, Any]:
        """Very small momentum heuristic used if ElizaOS is unavailable."""
        closes = [c[4] for c in ohlcv[-20:]] if ohlcv else []
        if len(closes) < 5:
            return {"action": "hold", "confidence": 0.0, "reason": "insufficient data"}

        short_ma = sum(closes[-5:]) / 5
        long_ma = sum(closes) / len(closes)
        if short_ma > 1.002 * long_ma:
            return {"action": "buy", "confidence": 0.58, "reason": "short MA above long MA"}
        if short_ma < 0.998 * long_ma:
            return {"action": "sell", "confidence": 0.58, "reason": "short MA below long MA"}
        return {"action": "hold", "confidence": 0.42, "reason": "flat trend"}

    def generate_signal(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        market_context is expected to contain keys like:
        - symbol
        - ohlcv
        - order_book
        - wallet_balances
        """
        ohlcv = market_context.get("ohlcv", [])
        if self.agent is None:
            return self._fallback_signal(ohlcv)

        prompt = f"{self.prompt}\nContext:\n{market_context}"
        try:
            response = self.agent.run(prompt)
            return {
                "action": response.get("action", "hold"),
                "confidence": response.get("confidence", 0.5),
                "reason": response.get("reason", "ElizaOS response"),
            }
        except Exception as exc:  # pragma: no cover - guardrail around LLM calls
            logger.error("ElizaOS failed: %s", exc)
            return {"action": "hold", "confidence": 0.0, "reason": str(exc)}
