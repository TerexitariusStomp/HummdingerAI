import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator

# Load .env once at import time
load_dotenv()


class Settings(BaseSettings):
    app_title: str = Field("ElizaOS Trading Bot", env="APP_TITLE")
    network_name: str = Field("ethereum", env="NETWORK_NAME")

    rpc_url: str = Field(..., env="RPC_URL")
    private_key: str = Field(..., env="PRIVATE_KEY")
    public_address: str = Field(..., env="PUBLIC_ADDRESS")

    flashbots_relay: str = Field("https://relay.flashbots.net", env="FLASHBOTS_RELAY")
    flashbots_block_priority_gwei: int = Field(5, env="FLASHBOTS_BLOCK_PRIORITY_GWEI")

    hummingbot_path: Optional[str] = Field(None, env="HUMMINGBOT_PATH")
    hummingbot_gateway: Optional[str] = Field(None, env="HUMMINGBOT_GATEWAY")
    hummingbot_strategy: str = Field("basic_arbitrage", env="HUMMINGBOT_STRATEGY")

    exchange_id: str = Field("binance", env="EXCHANGE_ID")
    exchange_api_key: Optional[str] = Field(None, env="EXCHANGE_API_KEY")
    exchange_secret: Optional[str] = Field(None, env="EXCHANGE_SECRET")

    class Config:
        case_sensitive = False

    @validator("rpc_url", "private_key", "public_address")
    def must_not_be_placeholder(cls, value: str) -> str:
        if not value or "your" in value.lower():
            raise ValueError("Set RPC_URL, PRIVATE_KEY, and PUBLIC_ADDRESS in your .env")
        return value

    @validator("hummingbot_path", always=True)
    def validate_hummingbot_sources(cls, value: Optional[str], values) -> Optional[str]:
        gateway = values.get("hummingbot_gateway")
        if not value and not gateway:
            # Allow empty but warn later in runtime; we avoid raising to keep GUI usable.
            return None
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def ensure_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing {path}. Copy config/example.env to {path} and fill it out."
        )
