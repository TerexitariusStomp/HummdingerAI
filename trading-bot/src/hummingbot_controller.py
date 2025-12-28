import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


class HummingbotController:
    """
    Thin helper to either launch Hummingbot locally or talk to an existing gateway/REST API.
    Strategy specifics are expected to live inside your Hummingbot repo; here we only push signals/config.
    """

    def __init__(
        self,
        strategy: str,
        hummingbot_path: Optional[str] = None,
        gateway_url: Optional[str] = None,
    ) -> None:
        self.strategy = strategy
        self.hummingbot_path = hummingbot_path
        self.gateway_url = gateway_url
        self.process: Optional[subprocess.Popen] = None

    def launch_subprocess(self) -> None:
        if not self.hummingbot_path:
            logger.info("No HUMMINGBOT_PATH set; skipping subprocess launch.")
            return

        executable = Path(self.hummingbot_path).expanduser()
        if not executable.exists():
            logger.error("Hummingbot executable not found at %s", executable)
            return

        env = os.environ.copy()
        cmd = [str(executable), "client"]
        logger.info("Launching Hummingbot: %s", " ".join(cmd))
        self.process = subprocess.Popen(cmd, env=env)

    def send_signal(self, signal: Dict, symbol: str) -> None:
        if self.gateway_url:
            self._send_signal_via_gateway(signal, symbol)
        elif self.process:
            logger.info("Hummingbot running locally; integrate CLI scripting here.")
        else:
            logger.warning("No Hummingbot target configured for signals.")

    def _send_signal_via_gateway(self, signal: Dict, symbol: str) -> None:
        if not self.gateway_url:
            return

        payload = {
            "strategy": self.strategy,
            "symbol": symbol,
            "signal": signal,
        }
        try:
            resp = requests.post(f"{self.gateway_url}/signals", json=payload, timeout=5)
            resp.raise_for_status()
            logger.info("Signal pushed to Hummingbot gateway: %s", payload)
        except requests.RequestException as exc:  # pragma: no cover - network guard
            logger.error("Failed to push signal to gateway: %s", exc)

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            logger.info("Stopping Hummingbot process...")
            self.process.terminate()
