"""High-level SANtricity REST client."""

from __future__ import annotations

import logging
from collections.abc import Mapping, MutableMapping
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from .auth.base import AuthStrategy
from .capabilities import CapabilityProfile, resolve_capabilities
from .config import ClientConfig
from .exceptions import AuthenticationError, RequestError
from .http import HttpResponse
from .http import request as http_request
from .resources import (
    ClonesResource,
    HostsResource,
    InterfacesResource,
    PoolsResource,
    SnapshotsResource,
    SystemResource,
    VolumeMappingsResource,
    VolumesResource,
)


logger = logging.getLogger(__name__)


class SANtricityClient:
    """Wrap SANtricity REST endpoints with helper methods."""

    def __init__(
        self,
        *,
        base_url: str,
        auth_strategy: AuthStrategy,
        verify_ssl: bool = True,
        timeout: float = 30.0,
        default_headers: Mapping[str, str] | None = None,
        query_defaults: Mapping[str, str] | None = None,
        session: requests.Session | None = None,
        release_version: str | None = None,
        system_id: str | None = None,
    ) -> None:
        base_includes_scope, parsed_system_id = self._detect_scoped_base(base_url)
        initial_system_id = system_id or parsed_system_id
        self.config = ClientConfig(
            base_url=base_url.rstrip("/"),
            verify_ssl=verify_ssl,
            timeout=timeout,
            default_headers=default_headers,
            query_defaults=query_defaults,
            release_version=release_version,
            system_id=initial_system_id,
        )
        self._suppress_insecure_warning_if_needed()
        self._session = session or requests.Session()
        self._auth = auth_strategy
        self._system_id: str | None = initial_system_id
        self._base_includes_scope = base_includes_scope
        self._inject_system_scope = not base_includes_scope
        self._scoped_prefix_cache: str | None = None
        self.capabilities: CapabilityProfile = resolve_capabilities(release_version)
        self._validate_auth_strategy()
        self.pools = PoolsResource(self)
        self.volumes = VolumesResource(self)
        self.interfaces = InterfacesResource(self)
        self.hosts = HostsResource(self)
        self.snapshots = SnapshotsResource(self)
        self.mappings = VolumeMappingsResource(self)
        self.clones = ClonesResource(self)
        self.system = SystemResource(self)

    # Context manager helpers -------------------------------------------------
    def __enter__(self) -> SANtricityClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - passthrough
        self.close()

    # Public API --------------------------------------------------------------
    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json_payload: Mapping[str, Any] | None = None,
        system_scope: bool = True,
    ) -> Any:
        url = self._resolve_url(path, system_scope=system_scope)
        headers = self._prepare_headers()
        merged_params = self._prepare_params(params)
        self._log_request(method, url)
        response = self._perform_request(
            method,
            url,
            params=merged_params,
            headers=headers,
            json_payload=json_payload,
        )
        return response.data

    def mappings_report(self) -> list[dict[str, Any]]:
        """Return a best-effort human-friendly view of volume mappings.

        This method performs the following calls (best-effort order):
        - GET /volumes
        - GET /storage-pools
        - GET /hosts
        - GET /host-groups
        - GET /volume-mappings

        The returned mapping rows are shallow copies of the mapping objects
        augmented with additional keys that are useful for human consumption
        and for the CLI table rendering (for example: `mappableObjectName`,
        `poolName`, `poolFreeSpace`, `hostLabel`, `hostGroup`).
        """
        vols = self.volumes.list() or []
        pools = self.pools.list() or []
        hosts = self.hosts.list() or []
        host_groups = self.hosts.list_groups() or []
        mappings = self.mappings.list() or []

        # Build quick lookup maps by common identifier fields. Map multiple
        # identifier keys to the same object so different payload shapes
        # (present in different SANtricity releases) resolve correctly.
        vol_by_id: dict[str, dict[str, Any]] = {}
        for v in vols:
            candidates = (
                v.get("volumeRef"),
                v.get("id"),
                v.get("mappableObjectId"),
                v.get("mappableObjectRef"),
            )
            for cand in candidates:
                if cand:
                    vol_by_id.setdefault(str(cand), v)

        pool_by_id: dict[str, dict[str, Any]] = {}
        for p in pools:
            candidates = (
                p.get("id"),
                p.get("volumeGroupRef"),
                p.get("volumeGroupId"),
                p.get("volumeGroupRef"),
            )
            for cand in candidates:
                if cand:
                    pool_by_id.setdefault(str(cand), p)

        host_by_ref: dict[str, dict[str, Any]] = {}
        for h in hosts:
            candidates = (h.get("hostRef"), h.get("id"), h.get("clusterRef"))
            for cand in candidates:
                if cand:
                    host_by_ref.setdefault(str(cand), h)

        group_by_cluster: dict[str, dict[str, Any]] = {}
        for g in host_groups:
            candidates = (g.get("clusterRef"), g.get("id"))
            for cand in candidates:
                if cand:
                    group_by_cluster.setdefault(str(cand), g)

        result: list[dict[str, Any]] = []
        for m in mappings:
            row: dict[str, Any] = dict(m)

            # Resolve volume info
            vid = (
                m.get("volumeRef")
                or m.get("mappableObjectId")
                or m.get("mappableObjectRef")
                or m.get("mappableObject")
            )
            if vid:
                vol = vol_by_id.get(str(vid))
                if vol:
                    row.setdefault("mappableObjectName", vol.get("name") or vol.get("label"))
                    # common capacity keys
                    for cap_key in ("capacity", "reportedSize", "currentVolumeSize"):
                        if cap_key in vol and vol.get(cap_key) is not None:
                            row.setdefault("capacity", vol.get(cap_key))
                            break
                    # pool lookup
                    pool_id = vol.get("volumeGroupRef") or vol.get("poolId") or vol.get("storagePoolId")
                    if pool_id:
                        pool = pool_by_id.get(str(pool_id))
                        if pool:
                            row.setdefault("poolName", pool.get("label") or pool.get("name"))
                            if pool.get("freeSpace") is not None:
                                row.setdefault("poolFreeSpace", pool.get("freeSpace"))
                            # RAID level best-effort
                            raid = pool.get("raidLevel")
                            if not raid:
                                extents = pool.get("extents")
                                if isinstance(extents, (list, tuple)) and extents:
                                    first = extents[0]
                                    if isinstance(first, Mapping):
                                        raid = first.get("raidLevel")
                            if raid:
                                row.setdefault("raidLevel", raid)

            # Resolve mapping target (host or host-group)
            target_id = m.get("targetId") or m.get("clusterRef") or m.get("hostRef") or m.get("hostGroup")
            if target_id:
                # Try hosts first
                host_obj = host_by_ref.get(str(target_id))
                if host_obj:
                    row.setdefault("hostLabel", host_obj.get("label") or host_obj.get("name"))
                    row.setdefault("hostRef", host_obj.get("hostRef") or host_obj.get("id"))
                    row.setdefault("targetLabel", row.get("hostLabel"))
                else:
                    group_obj = group_by_cluster.get(str(target_id))
                    if group_obj:
                        row.setdefault("hostGroup", group_obj.get("label") or group_obj.get("name"))
                        row.setdefault("clusterRef", group_obj.get("clusterRef") or group_obj.get("id"))
                        row.setdefault("targetLabel", row.get("hostGroup"))
                    else:
                        # last-resort: echo target id into a display key
                        row.setdefault("targetLabel", str(target_id))

            # Provide a normalized mapping id for display
            map_id = m.get("mapRef") or m.get("mappingRef") or m.get("id") or m.get("lunMappingRef")
            if map_id:
                row.setdefault("mappingRef", map_id)

            result.append(row)

        return result

    def close(self) -> None:
        self._session.close()

    # Internal helpers -------------------------------------------------------
    def _resolve_url(self, path: str, *, system_scope: bool) -> str:
        parsed = urlparse(path)
        if parsed.scheme and parsed.netloc:
            return path
        scoped_path = self._maybe_scope_path(path, system_scope=system_scope)
        relative_path = scoped_path.lstrip("/")
        return urljoin(f"{self.config.base_url}/", relative_path)

    def _maybe_scope_path(self, path: str, *, system_scope: bool) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        if not system_scope:
            return normalized
        if normalized.startswith("/storage-systems/"):
            return normalized
        if not self._inject_system_scope:
            return normalized
        prefix = self._system_scope_prefix()
        return f"{prefix}{normalized}"

    def _system_scope_prefix(self) -> str:
        if self._scoped_prefix_cache:
            return self._scoped_prefix_cache
        system_id = self._get_system_id()
        self._scoped_prefix_cache = f"/storage-systems/{system_id}"
        return self._scoped_prefix_cache

    def _get_system_id(self) -> str:
        if self._system_id:
            return self._system_id
        self._system_id = self._discover_system_id()
        self.config.system_id = self._system_id
        return self._system_id

    def _discover_system_id(self) -> str:
        payload = self.request("GET", "/storage-systems", system_scope=False)
        if isinstance(payload, list) and payload:
            first = payload[0]
            if isinstance(first, Mapping):
                candidate = first.get("wwn") or first.get("id")
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
        raise RequestError(
            "Unable to determine SANtricity storage-system identifier from /storage-systems."
        )

    def _prepare_headers(self) -> MutableMapping[str, str]:
        headers = self.config.resolved_headers()
        self._auth.apply(headers)
        return headers

    def _prepare_params(self, params: Mapping[str, str] | None) -> MutableMapping[str, str]:
        merged: MutableMapping[str, str] = self.config.resolved_query()
        if params:
            merged.update(params)
        return merged

    def _perform_request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, str] | None,
        headers: MutableMapping[str, str],
        json_payload: Mapping[str, Any] | None,
    ) -> HttpResponse:
        try:
            return http_request(
                self._session,
                method,
                url,
                params=params,
                headers=headers,
                json_payload=json_payload,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        except requests.HTTPError as exc:  # pragma: no cover - requests raises rarely
            raise AuthenticationError("Authentication failed") from exc
        except requests.RequestException as exc:
            reason = str(exc).strip() or exc.__class__.__name__
            raise RequestError(
                f"Failed to communicate with SANtricity API: {reason}", details=reason
            ) from exc

    def _log_request(self, method: str, url: str) -> None:
        system_id = self._system_id
        logger.info(
            "SANtricity request %s %s (system_id=%s)",
            method.upper(),
            url,
            system_id or "unspecified",
        )

    @staticmethod
    def _detect_scoped_base(base_url: str) -> tuple[bool, str | None]:
        parsed = urlparse(base_url)
        segments = [segment for segment in parsed.path.split("/") if segment]
        for index, segment in enumerate(segments):
            if segment == "storage-systems" and index + 1 < len(segments):
                return True, segments[index + 1]
        return False, None

    def _validate_auth_strategy(self) -> None:
        from .auth.jwt import JWTAuth

        if isinstance(self._auth, JWTAuth) and not self.capabilities.supports_jwt:
            raise AuthenticationError(
                "JWT authentication is unavailable on SANtricity release "
                f"{self.capabilities.describe_release()}"
            )

    def _suppress_insecure_warning_if_needed(self) -> None:
        if isinstance(self.config.verify_ssl, bool) and not self.config.verify_ssl:
            urllib3.disable_warnings(InsecureRequestWarning)
