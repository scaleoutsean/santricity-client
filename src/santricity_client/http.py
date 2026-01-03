"""HTTP utilities for SANtricity API access."""
from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

from requests import Response, Session

from .exceptions import RequestError, UnexpectedResponseError


@dataclass(slots=True)
class HttpResponse:
    """Typed response wrapper with helper accessors."""

    status_code: int
    data: Any
    headers: Mapping[str, str]


def ensure_success(response: Response) -> None:
    """Raise `RequestError` if the response signals a failure."""

    if 200 <= response.status_code < 300:
        return
    message = f"SANtricity API error {response.status_code}: {response.text[:200]}"
    raise RequestError(message, status_code=response.status_code, details=response.text)


def parse_json(response: Response) -> Any:
    """Parse JSON with helpful error context."""

    try:
        return response.json()
    except ValueError as exc:  # pragma: no cover - defensive
        raise UnexpectedResponseError("Response did not contain valid JSON") from exc


def request(
    session: Session,
    method: str,
    url: str,
    *,
    params: Mapping[str, str] | None = None,
    headers: MutableMapping[str, str] | None = None,
    json_payload: Mapping[str, Any] | None = None,
    timeout: float | tuple[float, float] | None = None,
    verify: bool = True,
) -> HttpResponse:
    """Make a request and return a parsed response envelope."""

    response = session.request(
        method=method,
        url=url,
        params=params,
        headers=headers,
        json=json_payload,
        timeout=timeout,
        verify=verify,
    )
    ensure_success(response)
    data = parse_json(response) if response.content else None
    return HttpResponse(status_code=response.status_code, data=data, headers=response.headers)
