from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    qdrant_url: str
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()