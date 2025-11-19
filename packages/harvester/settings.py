"""Application settings using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "production", "test"] = "development"

    # Database
    database_path: Path = Field(
        default=Path("data/mcps.db"),
        description="Path to SQLite database file",
    )
    database_echo: bool = Field(
        default=False,
        description="Echo SQL statements to stdout",
    )

    # GitHub API
    github_token: str | None = Field(
        default=None,
        description="GitHub personal access token for API requests",
    )

    # Application
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """Get async SQLite database URL."""
        # Ensure parent directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{self.database_path}"


# Global settings instance
settings = Settings()
