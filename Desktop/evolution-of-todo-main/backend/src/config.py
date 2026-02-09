from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Authentication
    AUTH_SECRET: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Phase III: AI Chatbot - OpenRouter Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4"
    MCP_SERVER_PORT: int = 8001
    CHAT_RATE_LIMIT: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_settings(self):
        """Validate critical settings are properly configured"""
        errors = []

        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is not set")

        if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be set and at least 32 characters long")

        if not self.AUTH_SECRET:
            errors.append("AUTH_SECRET is not set")

        # Phase III: Validate OpenRouter API key
        if not self.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is not set - AI chatbot will not function")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


settings = Settings()

# Validate settings on import
try:
    settings.validate_settings()
except ValueError as e:
    import sys
    print(f"CRITICAL CONFIGURATION ERROR: {e}", file=sys.stderr)
    print("Please check your .env file and ensure all required variables are set.", file=sys.stderr)
    # Don't exit in production, but log the error
    if settings.ENVIRONMENT == "development":
        raise
