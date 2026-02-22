"""Host abstractions."""

from __future__ import annotations

from typing import Any

from .base import ResourceBase


class HostsResource(ResourceBase):
    """Manage hosts and host groups."""

    def list(self) -> list[dict[str, Any]]:
        return self._get("/hosts")

    def get(self, host_ref: str) -> dict[str, Any]:
        return self._get(f"/hosts/{host_ref}")

    def add_initiator(
        self,
        host_ref: str,
        name: str,
        type: str = "iscsi",
        chap_secret: str | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        """Add an initiator to a host.

        Args:
            host_ref: The host reference.
            name: The initiator name (IQN for iSCSI, NQN for NVMe).
            type: The interface type, either "iscsi" (default) or "nvmeof".
            chap_secret: Optional CHAP secret (iSCSI only).
            label: Optional user label for the initiator.
        """
        payload = {
            "type": type,
            "port": name,
        }
        if label:
            payload["label"] = label
        if chap_secret:
            payload["iscsiChapSecret"] = chap_secret

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
