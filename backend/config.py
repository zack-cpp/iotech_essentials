import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "oee_gateway"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "change_me_in_production"

    # MQTT Broker
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""

    # Cloud HTTP target
    HTTP_TARGET_URL: str = "https://app.chainstrument.com"

    # Inspection MQTT topic
    INSPECT_MQTT_TOPIC: str = "counter/mesin/jobsend"

    # Gateway identity
    GATEWAY_ID: str = "GATEWAY_01"

    # Backend server
    BACKEND_PORT: int = 8000

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
