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

    # Redis Cache
    redis_url: str | None = Field(
        default=None,
        description="Full Redis URL (overrides host/port settings)",
    )
    redis_host: str = Field(
        default="localhost",
        description="Redis host",
    )
    redis_port: int = Field(
        default=6379,
        description="Redis port",
    )
    redis_db: int = Field(
        default=0,
        description="Redis database number",
    )
    redis_password: str | None = Field(
        default=None,
        description="Redis password (if authentication enabled)",
    )
    redis_pool_size: int = Field(
        default=10,
        description="Redis connection pool size",
    )
    redis_socket_timeout: int = Field(
        default=5,
        description="Redis socket timeout in seconds",
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable Redis caching",
    )
    cache_ttl_default: int = Field(
        default=300,
        description="Default cache TTL in seconds",
    )
    cache_fail_silently: bool = Field(
        default=True,
        description="Continue operation if cache fails",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: Literal["json", "text"] = Field(
        default="text",
        description="Log format (json for production, text for development)",
    )
    log_file: str | None = Field(
        default=None,
        description="Log file path (None for no file logging)",
    )
    log_rotation_size: int = Field(
        default=100,
        description="Log rotation size in MB",
    )
    log_retention: int = Field(
        default=10,
        description="Number of rotated log files to keep",
    )

    # Metrics & Monitoring
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics collection",
    )
    metrics_port: int = Field(
        default=9090,
        description="Prometheus metrics port",
    )

    # Error Tracking (Sentry)
    sentry_enabled: bool = Field(
        default=False,
        description="Enable Sentry error tracking",
    )
    sentry_dsn: str | None = Field(
        default=None,
        description="Sentry DSN for error tracking",
    )
    sentry_environment: str | None = Field(
        default=None,
        description="Sentry environment (defaults to environment setting)",
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        description="Sentry transaction traces sample rate (0.0-1.0)",
    )
    sentry_profiles_sample_rate: float = Field(
        default=0.1,
        description="Sentry profiling sample rate (0.0-1.0)",
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable API rate limiting",
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Default rate limit (requests per minute)",
    )
    rate_limit_storage_url: str | None = Field(
        default=None,
        description="Redis URL for rate limit storage (uses redis_url if not set)",
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host to bind to",
    )
    api_port: int = Field(
        default=8000,
        description="API port",
    )
    api_workers: int = Field(
        default=4,
        description="Number of API workers (uvicorn)",
    )
    api_reload: bool = Field(
        default=False,
        description="Enable auto-reload (development only)",
    )

    # CORS Configuration
    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS middleware",
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow CORS credentials",
    )

    # Security
    secret_key: str = Field(
        default="changeme-in-production-use-openssl-rand-hex-32",
        description="Secret key for JWT signing and encryption",
    )
    security_headers_enabled: bool = Field(
        default=True,
        description="Enable security headers (CSP, HSTS, etc.)",
    )
    hsts_enabled: bool = Field(
        default=True,
        description="Enable HSTS header (HTTPS only)",
    )

    # Compression
    compression_enabled: bool = Field(
        default=True,
        description="Enable gzip compression",
    )
    compression_minimum_size: int = Field(
        default=500,
        description="Minimum response size in bytes to compress",
    )
    compression_level: int = Field(
        default=6,
        description="Gzip compression level (1-9)",
    )

    # Feature Flags
    feature_social_media: bool = Field(
        default=True,
        description="Enable social media features",
    )
    feature_embeddings: bool = Field(
        default=False,
        description="Enable semantic embeddings (requires OpenAI)",
    )
    feature_background_tasks: bool = Field(
        default=True,
        description="Enable background task scheduler",
    )

    # OpenAI (for embeddings)
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for embeddings",
    )
    openai_model: str = Field(
        default="gpt-4-turbo",
        description="OpenAI model for text generation",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model for embeddings",
    )

    # Social Media API Keys
    reddit_client_id: str | None = Field(default=None, description="Reddit API client ID")
    reddit_client_secret: str | None = Field(default=None, description="Reddit API client secret")
    reddit_user_agent: str = Field(
        default="MCPS:v1.0.0",
        description="Reddit API user agent",
    )

    twitter_bearer_token: str | None = Field(default=None, description="Twitter API bearer token")
    twitter_api_key: str | None = Field(default=None, description="Twitter API key")
    twitter_api_secret: str | None = Field(default=None, description="Twitter API secret")

    youtube_api_key: str | None = Field(default=None, description="YouTube Data API key")

    # Supabase Configuration
    supabase_url: str = Field(
        default="",
        description="Supabase project URL (https://xxxxx.supabase.co)",
    )
    supabase_anon_key: str = Field(
        default="",
        description="Supabase anonymous/public API key",
    )
    supabase_service_role_key: str = Field(
        default="",
        description="Supabase service role key (admin access, bypasses RLS)",
    )
    supabase_jwt_secret: str = Field(
        default="",
        description="Supabase JWT secret for token verification",
    )

    # Supabase PostgreSQL Direct Connection (for SQLAlchemy ORM)
    supabase_db_password: str = Field(
        default="",
        description="Supabase PostgreSQL database password",
    )
    supabase_db_host: str = Field(
        default="",
        description="Supabase PostgreSQL host (db.xxxxx.supabase.co)",
    )

    # Supabase Storage
    supabase_storage_bucket: str = Field(
        default="mcps-files",
        description="Supabase Storage bucket name",
    )

    # Use local PostgreSQL or Supabase
    use_supabase: bool = Field(
        default=False,
        description="Use Supabase instead of local PostgreSQL",
    )

    @computed_field  # type: ignore[misc]
    @property
    def redis_url_computed(self) -> str:
        """Get Redis URL based on configuration.

        Returns:
            Redis connection URL
        """
        if self.redis_url:
            return self.redis_url

        # Build URL from components
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[misc]
    @property
    def db_url(self) -> str:
        """Get database URL based on configuration.

        Priority:
        1. Explicit DATABASE_URL environment variable
        2. Supabase PostgreSQL (if use_supabase is enabled)
        3. Local PostgreSQL (default for production)
        4. SQLite (fallback for development)
        """
        # If DATABASE_URL is explicitly set, use it
        if self.database_url:
            return self.database_url

        # If Supabase is enabled, use Supabase PostgreSQL
        if self.use_supabase and self.supabase_db_host and self.supabase_db_password:
            return (
                f"postgresql+asyncpg://postgres:{self.supabase_db_password}"
                f"@{self.supabase_db_host}:5432/postgres"
            )

        # If use_sqlite is enabled, use SQLite
        if self.use_sqlite:
            # Ensure parent directory exists
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{self.database_path}"

        # Default to local PostgreSQL (production)
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
