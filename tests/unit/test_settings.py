from openapi_schema_validator.settings import get_settings
from openapi_schema_validator.settings import reset_settings_cache


def test_compiled_validator_cache_size_env_is_cached(monkeypatch):
    monkeypatch.setenv(
        "OPENAPI_SCHEMA_VALIDATOR_COMPILED_VALIDATOR_CACHE_MAX_SIZE",
        "11",
    )
    reset_settings_cache()

    first = get_settings()
    assert first.compiled_validator_cache_max_size == 11

    monkeypatch.setenv(
        "OPENAPI_SCHEMA_VALIDATOR_COMPILED_VALIDATOR_CACHE_MAX_SIZE",
        "3",
    )
    second = get_settings()
    assert second.compiled_validator_cache_max_size == 11

    reset_settings_cache()
    third = get_settings()
    assert third.compiled_validator_cache_max_size == 3
