"""
Core configuration management
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # === Application ===
    app_name: str = "sigma-analyst"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # === API Keys - Exchange ===
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None

    okx_api_key: Optional[str] = None
    okx_api_secret: Optional[str] = None
    okx_passphrase: Optional[str] = None

    bybit_api_key: Optional[str] = None
    bybit_api_secret: Optional[str] = None

    # === API Keys - On-chain ===
    glassnode_api_key: Optional[str] = None
    cryptoquant_api_key: Optional[str] = None

    # === API Keys - AI/ML ===
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # === Database ===
    postgres_user: str = "sigma_user"
    postgres_password: str = "password"
    postgres_db: str = "sigma_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # === Redis ===
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # === Pinecone ===
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index_name: str = "sigma-knowledge"

    # === Celery ===
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # === Security ===
    secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # === CORS ===
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # === Agent Configuration ===
    agent_mode: str = "oneshot"  # oneshot | monitor
    agent_timezone: str = "Europe/Istanbul"
    agent_locale: str = "tr-TR"
    monitor_freq: str = "15m"
    heartbeat_minutes: int = 60
    cooldown_minutes: int = 60
    max_alerts_per_day: int = 8

    # === Risk Management ===
    max_position_size_pct: float = 0.20
    max_leverage: float = 3.0
    max_drawdown_pct: float = 0.15

    # === ML/RL Configuration ===
    ml_ensemble_models: List[str] = ["gradboost", "xgboost", "lightgbm"]
    ml_ensemble_weights: List[float] = [0.4, 0.35, 0.25]

    rl_algorithm: str = "decision_transformer"
    rl_training_episodes: int = 10000
    rl_learning_rate: float = 3e-5
    rl_batch_size: int = 256
    rl_context_length: int = 50

    # === Backtest Configuration ===
    backtest_initial_capital: float = 100000.0
    backtest_commission_rate: float = 0.0004  # 0.04%
    backtest_slippage_model: str = "volume_based"

    # === Monitoring ===
    prometheus_port: int = 9090
    grafana_port: int = 3001

    # === Data Sources ===
    data_sources: List[str] = [
        "binance", "okx", "bybit", "bitget", "mexc",
        "coinbase", "gateio", "glassnode", "cryptoquant"
    ]

    # === Paths ===
    @property
    def data_dir(self) -> str:
        return os.path.join(os.path.dirname(__file__), "../../data")

    @property
    def models_dir(self) -> str:
        return os.path.join(self.data_dir, "models")

    @property
    def checkpoints_dir(self) -> str:
        return os.path.join(self.models_dir, "checkpoints")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience exports
settings = get_settings()
