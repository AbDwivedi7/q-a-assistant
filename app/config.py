from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    WEATHER_API_BASE: str = "https://api.open-meteo.com/v1/forecast"
    ALPHA_VANTAGE_API_KEY: str | None = None
    STOCKS_PROVIDER: str = "yfinance"  # or "alphavantage"
    REDIS_URL: str | None = None
    API_AUTH_TOKEN: str | None = None
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # load on import; okay for small app