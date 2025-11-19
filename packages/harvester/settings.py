"""Application settings using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, field_validator
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

    # Database - PostgreSQL (Production)
    database_url: str | None = Field(
        default=None,
        description="Full database URL (overrides all other database settings)",
    )

    # PostgreSQL Connection Settings
    postgres_host: str = Field(
        default="localhost",
        description="PostgreSQL host",
    )
    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port",
    )
    postgres_user: str = Field(
        default="mcps",
        description="PostgreSQL username",
    )
    postgres_password: str = Field(
        default="mcps_password",
        description="PostgreSQL password",
    )
    postgres_db: str = Field(
        default="mcps",
        description="PostgreSQL database name",
    )

    # Connection Pool Settings
    db_pool_size: int = Field(
        default=20,
        description="Database connection pool size",
    )
    db_max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections beyond pool_size",
    )
    db_pool_recycle: int = Field(
        default=3600,
        description="Recycle connections after N seconds (prevents stale connections)",
    )
    db_pool_pre_ping: bool = Field(
        default=True,
        description="Test connections before using them",
    )
    db_echo: bool = Field(
        default=False,
        description="Echo SQL statements to stdout",
    )

    # Legacy SQLite Support (for backward compatibility)
    database_path: Path = Field(
        default=Path("data/mcps.db"),
        description="Path to SQLite database file (legacy/dev only)",
    )
    use_sqlite: bool = Field(
        default=False,
        description="Use SQLite instead of PostgreSQL (dev/testing only)",
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
    def db_url(self) -> str:
        """Get database URL based on configuration.

        Priority:
        1. Explicit DATABASE_URL environment variable
        2. PostgreSQL (default for production)
        3. SQLite (fallback for development)
        """
        # If DATABASE_URL is explicitly set, use it
        if self.database_url:
            return self.database_url

        # If use_sqlite is enabled, use SQLite
        if self.use_sqlite:
            # Ensure parent directory exists
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{self.database_path}"

        # Default to PostgreSQL (production)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL."""
        return "postgresql" in self.db_url

    @computed_field  # type: ignore[misc]
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return "sqlite" in self.db_url


# Global settings instance
settings = Settings()
