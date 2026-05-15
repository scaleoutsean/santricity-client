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

    def get_volume_by_name(self, name: str, pool_name: str | None = None) -> dict[str, Any] | None:
        """Find a volume by its name or label, optionally filtering by pool name.

        Args:
            name: The name or label of the volume.
            pool_name: Optional name or label of the storage pool containing the volume.

        Returns:
            The volume object if found, else None.
        """
        target_pool_ref = None
        if pool_name:
            pool = self._client.pools.get_by_name(pool_name)
            if not pool:
                return None
            target_pool_ref = pool.get("volumeGroupRef") or pool.get("id")

        for volume in self.list():
            if volume.get("label") == name or volume.get("name") == name:
                if target_pool_ref and volume.get("volumeGroupRef") != target_pool_ref:
                    continue
                return volume
        return None

    def delete(self, volume_ref: str) -> dict[str, Any]:
        return self._delete(f"/volumes/{volume_ref}")

    def create(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/volumes", payload)

    def map_to_host(self, volume_ref: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._post(f"/volumes/{volume_ref}/mappings", payload)

    def expand(
        self, volume_ref: str, expansion_size: float | int, unit: str = "bytes"
    ) -> dict[str, Any]:
        """Expand a volume to a new target capacity.

        Args:
            volume_ref: The volume reference.
            expansion_size: The new target capacity.
            unit: The unit of the expansion size.
                  Supported units: bytes, mb, gb, tb, mib, gib, tib.
                  mb/gb/tb are treated as decimal (powers of 1000).
                  mib/gib/tib are treated as binary (powers of 1024).

        Returns:
            A dictionary containing the expansion progress details.
        """
        unit_multipliers = {
            "bytes": 1,
            "b": 1,
            "mb": 1000**2,
            "gb": 1000**3,
            "tb": 1000**4,
            "mib": 1024**2,
            "gib": 1024**3,
            "tib": 1024**4,
        }

        normalized_unit = unit.lower()
        if normalized_unit not in unit_multipliers:
            raise ValueError(
                f"Invalid unit: {unit}. Supported units: {', '.join(unit_multipliers.keys())}"
            )

        size_bytes = int(expansion_size * unit_multipliers[normalized_unit])

        payload = {"expansionSize": size_bytes, "sizeUnit": "bytes"}

        return self._post(f"/volumes/{volume_ref}/expand", payload)

    def copy(
        self,
        source_id: str,
        target_id: str,
        priority: str = "priority3",
        online: bool = True,
        target_write_protected: bool = False,
        repository_candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a volume copy job.

        Args:
            source_id: The source volume reference.
            target_id: The target volume reference.
            priority: Copy priority (default: priority3).
            online: Whether the copy is online or offline.
            target_write_protected: Whether the target is write-protected during copy.
            repository_candidate: Optional repository payload for online copy.

        Returns:
            The volume copy job details.
        """
        payload = {
            "sourceId": source_id,
            "targetId": target_id,
            "copyPriority": priority,
            "targetWriteProtected": target_write_protected,
            "onlineCopy": online,
        }
        if online and repository_candidate:
            payload["repositoryCandidate"] = repository_candidate
            
        return self._post("/volume-copy-jobs", payload)

    def list_copies(self) -> list[dict[str, Any]]:
        """List active volume copy jobs.

        Returns:
            A list of volume copy jobs.
        """
        return self._get("/volume-copy-jobs")

    def copy_status(self) -> list[dict[str, Any]]:
        """Get progress for long-lived operations, including volume copies.

        Returns:
            A list of long-lived operations progress details.
        """
        response = self._post("/symbol/getLongLivedOpsProgress?verboseErrorResponse=true", {})
        return response.get("longLivedOpsProgress", [])

    def delete_copy(self, volcopy_ref: str, retain_repositories: bool = False) -> None:
        """Delete a volume copy job.

        Args:
            volcopy_ref: The volume copy job reference.
            retain_repositories: Whether to retain repositories used by the copy.
        """
        retain_str = "true" if retain_repositories else "false"
        self._delete(f"/volume-copy-jobs/{volcopy_ref}?retainRepositories={retain_str}")

    def update_copy(
        self,
        volcopy_ref: str,
        priority: str | None = None,
        target_write_protected: bool | None = None,
    ) -> dict[str, Any]:
        """Update properties of an existing volume copy job.

        Args:
            volcopy_ref: The volume copy job reference.
            priority: Intervene to change copy priority (e.g. priority0 to priority4).
            target_write_protected: Change target write protection state.

        Returns:
            The updated volume copy job details.
        """
        payload = {}
        if priority is not None:
            payload["copyPriority"] = priority
        if target_write_protected is not None:
            payload["targetWriteProtected"] = target_write_protected

        if not payload:
            raise ValueError("At least one attribute (priority or target_write_protected) must be specified for update.")

        return self._post(f"/volume-copy-jobs/{volcopy_ref}", payload)

