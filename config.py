"""Configuration — loaded from environment variables / .env file."""

import threading

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    private_key: SecretStr = Field(
        description="Wallet private key (0x-prefixed hex, 66 chars)"
    )
    wallet_address: str = Field(
        description="Wallet address (0x-prefixed, 42 chars)"
    )
    polygon_rpc_url: str = Field(
        default="https://polygon-rpc.com",
        description="Polygon mainnet RPC endpoint",
    )
    poll_interval: int = Field(
        default=120,
        description="Seconds between redemption polls",
        ge=10,
    )


_settings: Settings | None = None
_lock = threading.Lock()


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        with _lock:
            if _settings is None:
                _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset cached settings (used in tests)."""
    global _settings
    with _lock:
        _settings = None
