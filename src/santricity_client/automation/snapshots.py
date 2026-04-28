"""Snapshot workflow helpers that orchestrate multiple raw API calls."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import-time guard
    from ..client import SANtricityClient


from collections.abc import Mapping, Sequence
from typing import Any

from ..exceptions import RequestError


def _coerce_int_default(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _pick_group_field_int(group: Mapping[str, Any], *keys: str) -> int:
    for key in keys:
        if key in group:
            value = _coerce_int_default(group.get(key), 0)
            if value != 0:
                return abs(value)
    return 0


def _snapshot_schedule_counts(schedules: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for schedule in schedules:
        target = schedule.get("targetObject")
        if not target:
            continue
        key = str(target)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _choose_snapshot_group_for_auto(
    groups: Sequence[Mapping[str, Any]],
    schedules: Sequence[Mapping[str, Any]],
    utilization: Sequence[Mapping[str, Any]],
    repositories: Sequence[Mapping[str, Any]],
    *,
    volume_ref: str,
    include_schedule_owned_groups: bool,
    min_free_percent: float,
    max_repo_group_capacity_percent: float,
    max_repo_volumes_per_group: int,
) -> tuple[str | None, dict[str, Any] | None]:
    schedule_counts = _snapshot_schedule_counts(schedules)
    util_by_group_ref: dict[str, Mapping[str, Any]] = {
        str(item.get("groupRef") or ""): item for item in utilization if item.get("groupRef")
    }
    repo_by_ref: dict[str, Mapping[str, Any]] = {
        str(item.get("id") or item.get("repositoryRef") or item.get("concatRef") or ""): item
        for item in repositories
        if item.get("id") or item.get("repositoryRef") or item.get("concatRef")
    }

    eligible: list[tuple[int, int, str]] = []
    grow_candidates: list[tuple[int, int, int, str, dict[str, Any]]] = []

    for group in groups:
        group_ref = str(group.get("pitGroupRef") or group.get("id") or "")
        if not group_ref:
            continue
        if str(group.get("baseVolume") or "") != volume_ref:
            continue

        schedule_count = schedule_counts.get(group_ref, 0)
        if schedule_count > 0 and not include_schedule_owned_groups:
            continue

        util = util_by_group_ref.get(group_ref, {})
        available = _coerce_int_default(util.get("pitGroupBytesAvailable"), 0)
        used = _coerce_int_default(util.get("pitGroupBytesUsed"), 0)

        base_bytes = _pick_group_field_int(group, "maxBaseCapacity", "baseVolumeCapacity")
        if base_bytes <= 0:
            base_bytes = available + used

        min_free_bytes = int(base_bytes * (min_free_percent / 100.0)) if base_bytes > 0 else 0
        repo_capacity_bytes = _pick_group_field_int(group, "repositoryCapacity")
        if repo_capacity_bytes <= 0:
            repo_capacity_bytes = available + used

        current_repo_percent = (repo_capacity_bytes / base_bytes * 100.0) if base_bytes > 0 else 0.0

        snapshot_count = _coerce_int_default(group.get("snapshotCount"), 0)
        if available >= min_free_bytes:
            eligible.append((available, -snapshot_count, group_ref))
            continue

        repository_ref = str(group.get("repositoryVolume") or "")
        repository = repo_by_ref.get(repository_ref, {}) if repository_ref else {}
        member_count = _pick_group_field_int(
            repository,
            "memberCount",
            "totalRepositoryVolumes",
            "repositoryVolumeCount",
            "volumeCount",
        )

        if current_repo_percent >= max_repo_group_capacity_percent:
            continue

        if member_count <= 0 and isinstance(repository.get("members"), list):
            member_count = len(repository["members"])
        if member_count >= max_repo_volumes_per_group:
            continue

        grow_candidates.append(
            (
                available,
                -snapshot_count,
                -member_count,
                group_ref,
                {
                    "groupRef": group_ref,
                    "repositoryRef": repository_ref,
                    "baseVolumeRef": str(group.get("baseVolume") or ""),
                    "availableBytes": available,
                    "minFreeBytes": min_free_bytes,
                    "memberCount": member_count,
                },
            )
        )

    if eligible:
        eligible.sort(reverse=True)
        return eligible[0][2], None

    if grow_candidates:
        grow_candidates.sort(reverse=True)
        return None, grow_candidates[0][4]

    return None, None


class SnapshotsAutomation:
    """Namespace for higher-level snapshot automation workflows."""

    def __init__(self, client: SANtricityClient) -> None:
        self._client = client

    def _list_schedules_best_effort(self) -> list[dict[str, Any]]:
        try:
            return self._client.snapshots.list_schedules()
        except RequestError as exc:
            if exc.status_code in {404, 405}:
                return []
            raise

    def auto_create_snapshot(
        self,
        *,
        group_ref: str | None = None,
        volume_ref: str | None = None,
        auto: bool = False,
        include_schedule_owned_groups: bool = False,
        min_free_percent: float = 0.0,
        auto_grow_if_needed: bool = True,
        growth_step_percent: int = 10,
        max_repo_group_capacity_percent: float = 100.0,
        max_repo_volumes_per_group: int = 16,
    ) -> dict[str, Any]:
        """Create a snapshot in an existing snapshot group, with auto-selection if requested.

        If `auto` is False, `group_ref` must be provided.
        """
        if not group_ref and not auto:
            raise ValueError("Either group_ref or auto must be provided.")
        if auto and not group_ref and not volume_ref:
            raise ValueError("volume_ref is required when using auto without group_ref.")

        resolved_group_ref = group_ref
        groups: list[dict[str, Any]] | None = None

        if auto and not resolved_group_ref:
            groups = self._client.snapshots.list_groups()
            schedules = self._list_schedules_best_effort()
            utilization = self._client.snapshots.list_group_repo_utilization()
            repositories = self._client.snapshots.list_repositories()

            resolved_group_ref, grow_target = _choose_snapshot_group_for_auto(
                groups,
                schedules,
                utilization,
                repositories,
                volume_ref=volume_ref or "",
                include_schedule_owned_groups=include_schedule_owned_groups,
                min_free_percent=min_free_percent,
                max_repo_group_capacity_percent=max_repo_group_capacity_percent,
                max_repo_volumes_per_group=max_repo_volumes_per_group,
            )

            if not resolved_group_ref and grow_target and auto_grow_if_needed:
                candidates = self._client.snapshots.get_repo_group_candidates_single(
                    base_volume_ref=str(grow_target.get("baseVolumeRef") or ""),
                    percent_capacity=growth_step_percent,
                    use_free_repository_volumes=False,
                )
                candidate = (
                    candidates[0].get("candidate")
                    if isinstance(candidates, list) and candidates
                    else None
                )
                repository_ref = str(grow_target.get("repositoryRef") or "")
                if candidate and repository_ref:
                    self._client.snapshots.expand_repository(
                        repository_ref=repository_ref,
                        expansion_candidate=candidate,
                    )
                    resolved_group_ref = str(grow_target.get("groupRef") or "")

            if not resolved_group_ref:
                raise RuntimeError("No eligible snapshot group found under current policy.")

        if not resolved_group_ref:
            raise RuntimeError("A snapshot group reference could not be resolved.")

        if volume_ref:
            if groups is None:
                groups = self._client.snapshots.list_groups()
            selected_group = next(
                (
                    g
                    for g in groups
                    if str(g.get("pitGroupRef") or g.get("id") or "") == resolved_group_ref
                ),
                None,
            )
            if selected_group is None:
                raise RuntimeError(f"Snapshot group '{resolved_group_ref}' was not found.")
            if str(selected_group.get("baseVolume") or "") != volume_ref:
                raise RuntimeError("The provided group-ref does not belong to the provided volume.")

        return self._client.snapshots.create_snapshot(resolved_group_ref)
