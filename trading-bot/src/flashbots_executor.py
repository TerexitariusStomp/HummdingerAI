import logging
from typing import Any, Dict, List, Optional

from web3 import HTTPProvider, Web3
from web3.middleware import geth_poa_middleware

logger = logging.getLogger(__name__)

try:
    from eth_account import Account  # type: ignore
    from flashbots import flashbots  # type: ignore
except ImportError:
    Account = None
    flashbots = None


class FlashbotsExecutor:
    """Minimal Flashbots helper to send atomic bundles/flash loans for custom tokens."""

    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        relay_endpoint: str,
        block_priority_gwei: int = 5,
    ) -> None:
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.relay_endpoint = relay_endpoint
        self.block_priority_gwei = block_priority_gwei
        self.web3: Optional[Web3] = None
        self.signer = None

    def connect(self) -> None:
        if Account is None or flashbots is None:
            logger.warning(
                "flashbots/eth-account packages not installed; bundle sending disabled."
            )
            return

        self.web3 = Web3(HTTPProvider(self.rpc_url))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.signer = Account.from_key(self.private_key)
        flashbots(self.web3, self.signer, self.relay_endpoint)
        logger.info("Connected to Flashbots relay %s", self.relay_endpoint)

    def build_bundle(self, txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach defaults to the raw tx dicts."""
        if self.web3 is None:
            return []

        gas_price = self.web3.to_wei(self.block_priority_gwei, "gwei")
        bundle = []
        for tx in txns:
            tx.setdefault("gasPrice", gas_price)
            tx.setdefault("nonce", self.web3.eth.get_transaction_count(tx["from"]))
            bundle.append(tx)
        return bundle

    def send_bundle(self, bundle: List[Dict[str, Any]], target_block: Optional[int] = None) -> None:
        if self.web3 is None or flashbots is None or self.signer is None:
            logger.warning("Flashbots not ready; skip bundle submit.")
            return

        latest = self.web3.eth.block_number
        target = target_block or latest + 1
        logger.info("Submitting bundle for block %s", target)
        try:
            flashbots(self.web3, self.signer, self.relay_endpoint).send_bundle(
                bundle, target_block_number=target
            )
        except Exception as exc:  # pragma: no cover - network guard
            logger.error("Flashbots bundle failed: %s", exc)
