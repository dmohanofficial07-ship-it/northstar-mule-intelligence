from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Northstar Mule Account Intelligence"
    environment: str = "development"
    database_url: str = "sqlite:///./northstar.db"
    jwt_secret: str = "change-this-secret-outside-local-development"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "northstar-demo"
    kafka_bootstrap_servers: str = "localhost:9092"
    cors_origins: str = "http://localhost:8000,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
