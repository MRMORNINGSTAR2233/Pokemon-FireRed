"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Groq AI Configuration
    groq_api_key: str = ""

    # Emulator Configuration
    mgba_http_host: str = "localhost"
    mgba_http_port: int = 5000

    # Game Configuration
    rom_path: Path = Path("./rom.gba")
    save_state_dir: Path = Path("./data/saves")

    # Server Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    @property
    def mgba_http_url(self) -> str:
        """Get the full mGBA-http base URL."""
        return f"http://{self.mgba_http_host}:{self.mgba_http_port}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
