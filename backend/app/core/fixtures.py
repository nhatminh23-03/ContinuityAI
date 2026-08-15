"""Loads the shared contract fixtures.

Temporary: routes return these payloads until the real engines exist. Both sides read
the same files, so a shape disagreement surfaces immediately rather than on integration
day. docs/API_CONTRACT.md section 14.
"""

import json
from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.core.errors import NotFoundError


@lru_cache(maxsize=None)
def load(name: str) -> Any:
    path = settings.fixtures_path / f"{name}.json"
    if not path.exists():
        raise NotFoundError(f"Fixture '{name}' not found.", {"path": str(path)})
    return json.loads(path.read_text())
