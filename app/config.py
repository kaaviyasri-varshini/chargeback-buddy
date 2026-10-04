"""Application configuration and settings."""

from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "chargeback_buddy"
    
    # PayPal API
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_base_url: str = "https://api-m.sandbox.paypal.com"
    paypal_webhook_id: str = ""
    
    # AI
    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-4-20250514"
    
    # Application
    demo_mode: bool = True
    fighting_cost: Decimal = Decimal("25.00")
    risk_buffer: Decimal = Decimal("10.00")
    auto_approve_enabled: bool = False
    auto_approve_max_amount: Decimal = Decimal("20.00")
    auto_approve_min_win_prob: float = 0.85
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    
    @property
    def mongodb_test_db_name(self) -> str:
        """Test database name."""
        return f"{self.mongodb_db_name}_test"


# Global settings instance
settings = Settings()
