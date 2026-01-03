"""Host abstractions."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import ResourceBase


class HostsResource(ResourceBase):
    """Manage hosts and host groups."""

    def list(self) -> list[dict[str, Any]]:
        return self._get("/hosts")

    def get(self, host_ref: str) -> dict[str, Any]:
        return self._get(f"/hosts/{host_ref}")

    def add_initiator(self, host_ref: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/hosts/{host_ref}/initiators", payload)

    def list_groups(self) -> list[dict[str, Any]]:
        return self._get("/host-groups")

    def find_host(self, label: str) -> dict[str, Any] | None:
        for host in self.list():
            if host.get("label") == label:
                return host
        return None

    def find_group(self, label: str) -> dict[str, Any] | None:
        for group in self.list_groups():
            if group.get("label") == label:
                return group
        return None
