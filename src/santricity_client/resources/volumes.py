"""Volume operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import ResourceBase


class VolumesResource(ResourceBase):
    """Interact with SANtricity volumes."""

    def list(self) -> list[dict[str, Any]]:
        return self._get("/volumes")

    def get(self, volume_ref: str) -> dict[str, Any]:
        return self._get(f"/volumes/{volume_ref}")

    def delete(self, volume_ref: str) -> dict[str, Any]:
        return self._delete(f"/volumes/{volume_ref}")

    def create(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/volumes", payload)

    def map_to_host(self, volume_ref: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/volumes/{volume_ref}/mappings", payload)
