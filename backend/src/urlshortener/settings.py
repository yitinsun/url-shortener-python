"""Environment-backed settings. Lab defaults are for local use only."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_env: str = "dev"
    app_base_url: str = "http://localhost:8080"
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str | None = None
    db_user: str = "root"
    db_password: str = "Tiger"
    docs_enabled: bool | None = None

    @model_validator(mode="after")
    def fill_database_name(self) -> "Settings":
        if not self.db_name:
            self.db_name = "shortener_prod" if self.app_env == "prod" else "shortener_dev"
        if self.docs_enabled is None:
            self.docs_enabled = self.app_env != "prod"
        return self

    @property
    def base_url(self) -> str:
        return self.app_base_url.rstrip("/")
