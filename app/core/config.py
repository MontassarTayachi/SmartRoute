from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded depuis le fichier .env."""

    MONGO_URI: str = Field(default="mongodb://localhost:27017", env="MONGO_URI")
    MONGO_DB: str = Field(default="smartRoute", env="MONGO_DB")

    JWT_SECRET: str = Field(default="change-me-securely", env="JWT_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_EXPIRE_MINUTES")
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_EXPIRE_DAYS")

    BCRYPT_ROUNDS: int = Field(default=12, env="BCRYPT_ROUNDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
