import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    values = os.environ if env is None else env
    database_url = values.get("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return Settings(database_url=database_url)


@lru_cache
def get_settings() -> Settings:
    return load_settings()
