from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class OpenAPISchemaValidatorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENAPI_SCHEMA_VALIDATOR_",
        extra="ignore",
    )

    validate_cache_max_size: int = Field(default=128, ge=0)


@lru_cache(maxsize=1)
def get_settings() -> OpenAPISchemaValidatorSettings:
    return OpenAPISchemaValidatorSettings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
