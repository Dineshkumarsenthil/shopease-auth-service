"""Central configuration. Every value comes from environment variables / .env."""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ShopEase Authentication Service"
    APP_VERSION: str = "1.0.0"

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "auth_user"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "shopease_auth_db"

    # Optional full override (used by automated tests with SQLite)
    DATABASE_URL: Optional[str] = None

    JWT_SECRET_KEY: str            # required - no default on purpose
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )


settings = Settings()
