"""Snapshot helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import ResourceBase


class SnapshotsResource(ResourceBase):
    """Interact with snapshot groups, images, volumes, repositories, and schedules."""

    def list_groups(self) -> list[dict[str, Any]]:
        return self._get("/snapshot-groups")

    def create_group(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._post("/snapshot-groups", payload)

    def list_images(self, group_ref: str) -> list[dict[str, Any]]:
        """List snapshot images scoped to a specific snapshot group."""
        return self._get(f"/snapshot-groups/{group_ref}/images")

    def create_image(self, group_ref: str) -> dict[str, Any]:
        """Create a new snapshot image in the given snapshot group."""
        return self._post(f"/snapshot-groups/{group_ref}/images", {})

    def delete_image(self, image_ref: str) -> None:
        """Delete a snapshot image by its pitRef / id."""
        self._delete(f"/snapshot-images/{image_ref}")

    def list_all_images(self) -> list[dict[str, Any]]:
        """List all snapshot images across all snapshot groups."""
        return self._get("/snapshot-images")

    def list_volumes(self) -> list[dict[str, Any]]:
        """List snapshot volumes (linked clones and read-only views)."""
        return self._get("/snapshot-volumes")

    def list_repositories(self) -> list[dict[str, Any]]:
        """List concatenated repository volumes backing snapshot groups and linked clones."""
        return self._get("/repositories/concat")

    def list_group_repo_utilization(self) -> list[dict[str, Any]]:
        """List repository utilization for each snapshot group."""
        return self._get("/snapshot-groups/repository-utilization")

    def list_volume_repo_utilization(self) -> list[dict[str, Any]]:
        """List repository utilization for each snapshot volume (linked clone)."""
        return self._get("/snapshot-volumes/repository-utilization")

    def list_async_mirror_repo_utilization(self) -> list[dict[str, Any]]:
        """List repository utilization for async mirror pairs (all-flash arrays may return 404)."""
        return self._get("/async-mirrors/pairs/repository-utilization")

    def list_consistency_group_members(self) -> list[dict[str, Any]]:
        """List volumes that are members of consistency groups."""
        return self._get("/consistency-groups/member-volumes")

    def list_schedules(self) -> list[dict[str, Any]]:
        """List snapshot schedules tied to snapshot groups."""
        return self._get("/snapshot-schedules")
