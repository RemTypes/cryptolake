from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from cryptolake.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def get_data_dir(settings: Settings = Depends(get_settings)) -> Path:
    """Return settings.data_dir, ensure it exists."""
    data_dir = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


DataDir = Annotated[Path, Depends(get_data_dir)]
