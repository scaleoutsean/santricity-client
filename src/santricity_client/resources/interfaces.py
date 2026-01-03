"""Interface module."""
from __future__ import annotations

from typing import Any

from .base import ResourceBase


class InterfacesResource(ResourceBase):
    """Access controller interface metadata."""

    def list(self) -> list[dict[str, Any]]:
        return self._get("/interfaces")

    def get(self, interface_id: str) -> dict[str, Any]:
        return self._get(f"/interfaces/{interface_id}")
