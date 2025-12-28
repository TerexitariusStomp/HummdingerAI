# Trading Bot (ElizaOS + Hummingbot + Flashbots)

New prototype folder for an agentic trading bot that marries ElizaOS decision making with Hummingbot's execution engine, CCXT for exchange connectivity, Flashbots flash-loan routing, and a small Streamlit GUI built around live on-chain data.

## What lives here
- `src/eliza_agent.py` — hooks into ElizaOS to turn prompts + market context into trade signals.
- `src/market_data.py` — CCXT-driven market fetches (tickers, OHLCV) for centralized and EVM DEX endpoints; on-chain/DEX data is sourced only through CCXT to stay version-aligned.
- `src/hummingbot_controller.py` — thin orchestrator for launching/controlling a Hummingbot strategy process or API.
- `src/flashbots_executor.py` — Web3 + Flashbots bundle helper for custom-token atomic execution/flash loans.
- `src/gui.py` — Streamlit UI that leans on blockchain data to display signals, balances, and execution status.
- `src/main.py` — entrypoint wiring everything together.
- `config/example.env` — minimal environment variables you must set before running.
- `requirements.txt` — Python dependencies.

## Setup
1) Create a virtualenv and install deps:
   ```bash
   cd trading-bot
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
   Hummingbot and ElizaOS are large; consider installing them from their official repos if wheels are unavailable.
2) Copy `config/example.env` to `.env` and fill in RPC URLs, private keys (for Flashbots), and exchange API keys as needed.
3) Ensure you have a running Hummingbot instance accessible either via CLI or its REST/gateway interface. Update `HUMMINGBOT_PATH` or `HUMMINGBOT_GATEWAY` accordingly.

## Running
- GUI + services (dev mode):
  ```bash
  # from trading-bot/
  streamlit run src/gui.py
  ```
- Headless signal loop (no GUI):
  ```bash
  python src/main.py
  ```

## Staying updated with upstreams
- Run `./scripts/update_upstreams.sh` regularly to pull the latest ElizaOS / Hummingbot / Flashbots (via git if paths are set; otherwise pip upgrades) and refresh local Python dependencies.
- Keep `HUMMINGBOT_PATH`, `ELIZAOS_PATH`, and `FLASHBOTS_PATH` env vars pointed at your clones to ensure `git pull` picks up upstream changes.
- DEX data is intentionally sourced only via CCXT; avoid adding alternate DEX clients so updates stay centralized through CCXT releases.

## Notes on the stacks
- **ElizaOS**: This project expects an ElizaOS agent package installed and reachable in `PYTHONPATH`. See `src/eliza_agent.py` for the adapter stub and drop your prompt/skills there.
- **Hummingbot**: `src/hummingbot_controller.py` shows both a subprocess launcher and an HTTP gateway client. Pick one and set credentials/ports. Strategies are expected to be authored in your Hummingbot repo; this project only pushes config/signal updates.
- **CCXT**: Used in `src/market_data.py` to keep the UI and agent supplied with fresh orderbook/OHLCV data.
- **Flashbots**: `src/flashbots_executor.py` contains a minimal bundle submitter for atomic execution/flash loans on custom tokens. You need funded keys plus MEV relay endpoints.

## Roadmap / TODO
- Flesh out concrete Hummingbot strategy templates and parametrization.
- Connect ElizaOS callbacks directly into Hummingbot order submissions.
- Harden Flashbots bundle crafting (gas estimation, retries, simulation).
- Add persistence (sqlite) for signals/trade history and richer risk controls.
