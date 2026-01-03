import pytest
import requests
from urllib3.exceptions import InsecureRequestWarning

from santricity_client import SANtricityClient
from santricity_client.auth.basic import BasicAuth
from santricity_client.auth.jwt import JWTAuth
from santricity_client.exceptions import AuthenticationError, RequestError


def test_pools_list_returns_payload(requests_mock):
    client = SANtricityClient(
        base_url="https://array/devmgr/v2",
        auth_strategy=BasicAuth("u", "p"),
        system_id="demo",
    )
    requests_mock.get(
        "https://array/devmgr/v2/storage-systems/demo/storage-pools",
        json=[{"label": "poolA"}],
    )

    pools = client.pools.list()

    assert pools == [{"label": "poolA"}]


def test_jwt_auth_header_is_sent(requests_mock):
    auth = JWTAuth(token="abc123")
    client = SANtricityClient(
        base_url="https://array/devmgr/v2",
        auth_strategy=auth,
        system_id="demo",
    )
    matcher = requests_mock.get(
        "https://array/devmgr/v2/storage-systems/demo/volumes",
        json=[],
    )

    client.volumes.list()

    assert matcher.last_request.headers["Authorization"] == "Bearer abc123"


def test_jwt_rejected_for_legacy_release():
    auth = JWTAuth(token="legacy")
    with pytest.raises(AuthenticationError):
        SANtricityClient(
            base_url="https://array/devmgr/v2",
            auth_strategy=auth,
            release_version="11.70",
        )


def test_client_discovers_system_id_when_missing(requests_mock):
    requests_mock.get(
        "https://array/devmgr/v2/storage-systems",
        json=[{"wwn": "auto123"}],
    )
    requests_mock.get(
        "https://array/devmgr/v2/storage-systems/auto123/hosts",
        json=[{"label": "hostA"}],
    )
    client = SANtricityClient(
        base_url="https://array/devmgr/v2",
        auth_strategy=BasicAuth("u", "p"),
    )

    hosts = client.hosts.list()

    assert hosts[0]["label"] == "hostA"


def test_request_logging_includes_system_id(caplog, requests_mock):
    client = SANtricityClient(
        base_url="https://array/devmgr/v2",
        auth_strategy=BasicAuth("u", "p"),
        system_id="demo123",
    )
    requests_mock.get(
        "https://array/devmgr/v2/storage-systems/demo123/storage-pools",
        json=[],
    )

    with caplog.at_level("INFO", logger="santricity_client.client"):
        client.pools.list()

    assert "system_id=demo123" in caplog.text


def test_request_error_includes_root_cause():
    class ExplodingSession:
        def request(self, *args, **kwargs):  # pragma: no cover - helper
            raise requests.exceptions.SSLError("CERTIFICATE_VERIFY_FAILED")

        def close(self):  # pragma: no cover - helper
            pass

    client = SANtricityClient(
        base_url="https://array/devmgr/v2",
        auth_strategy=BasicAuth("u", "p"),
        system_id="demo",
        session=ExplodingSession(),
    )

    with pytest.raises(RequestError) as excinfo:
        client.pools.list()

    assert "CERTIFICATE_VERIFY_FAILED" in str(excinfo.value)


def test_disables_insecure_warning_when_verify_disabled(monkeypatch):
    captured: list[object] = []

    def fake_disable(warning):  # pragma: no cover - helper
        captured.append(warning)

    monkeypatch.setattr(
        "santricity_client.client.urllib3.disable_warnings",
        fake_disable,
    )

    SANtricityClient(
        base_url="https://array/devmgr/v2",
        auth_strategy=BasicAuth("u", "p"),
        system_id="demo",
        verify_ssl=False,
    )

    assert captured and captured[0] is InsecureRequestWarning
