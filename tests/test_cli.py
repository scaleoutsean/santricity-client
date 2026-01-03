import json

import pytest
import typer
from typer.testing import CliRunner

from santricity_client.cli import _build_client, app

runner = CliRunner()

SYSTEM_ID = "600A098000F63714"


def test_system_version_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/firmware/embedded-firmware/1/versions",
        json={
            "codeVersions": [
                {"codeModule": "bundleDisplay", "versionString": "11.90R2"},
                {"codeModule": "management", "versionString": "11.90.00.9029"},
            ]
        },
    )
    requests_mock.get(
        "https://array/devmgr/utils/buildinfo",
        json={
            "components": [
                {"name": "symbolapi", "version": "v1190api9"},
                {"name": "symbolversion", "version": "241"},
            ]
        },
    )

    result = runner.invoke(
        app,
        [
            "system",
            "version",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "11.90R2" in result.stdout


def test_pools_list_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools",
        json=[{"label": "poolA"}],
    )

    result = runner.invoke(
        app,
        [
            "pools",
            "list",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "poolA" in result.stdout


def test_pools_list_cli_json_output(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools",
        json=[{"label": "poolA"}],
    )

    result = runner.invoke(
        app,
        [
            "pools",
            "list",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["label"] == "poolA"


def test_volumes_create_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "0400" in result.stdout
    payload = requests_mock.last_request.json()
    assert payload["poolId"] == "0400"
    assert payload["name"] == "demo"


def test_volumes_check_names_cli_detects_duplicates(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[
            {"name": "db", "volumeRef": "1"},
            {"name": "db", "volumeRef": "2"},
            {"name": "logs", "volumeRef": "3"},
        ],
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "check-names",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 1
    assert "duplicate" in result.stderr.lower()


def test_volumes_check_names_cli_unique(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[
            {"name": "db", "volumeRef": "1"},
            {"name": "logs", "volumeRef": "2"},
        ],
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "check-names",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "unique" in result.stdout.lower()


def test_volumes_create_cli_blocks_duplicate_names(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"name": "demo", "volumeRef": "1"}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 1
    assert requests_mock.call_count == 1  # only the /volumes GET should fire


def test_volumes_create_cli_allows_duplicate_when_overridden(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--allow-duplicate-name",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0


def test_volumes_create_cli_fallbacks_to_legacy_endpoint(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        status_code=404,
        json={"message": "missing"},
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert requests_mock.call_count == 3


def test_mappings_list_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/v2/volume-mappings",
        json=[{"mappingRef": "m1"}],
    )

    result = runner.invoke(
        app,
        [
            "mappings",
            "list",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "m1" in result.stdout


def test_mappings_create_cli_with_host_resolution(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/hosts",
        json=[{"label": "apphost", "hostRef": "hostRef01"}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/v2/volume-mappings",
        json={"mappingRef": "map1"},
    )

    result = runner.invoke(
        app,
        [
            "mappings",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--volume-ref",
            "vol1",
            "--host",
            "apphost",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "map1" in result.stdout
    payload = requests_mock.request_history[-1].json()
    assert payload["mappableObjectId"] == "vol1"
    assert payload["targetId"] == "hostRef01"


def test_hosts_membership_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/hosts",
        json=[
            {
                "label": "app1",
                "hostRef": "hostRef01",
                "clusterRef": "cluster01",
            }
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/host-groups",
        json=[{"label": "prod-cluster", "clusterRef": "cluster01"}],
    )

    result = runner.invoke(
        app,
        [
            "hosts",
            "membership",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "prod-cluster" in result.stdout


def test_build_client_accepts_cert_path(monkeypatch, tmp_path):
    cert = tmp_path / "ca.pem"
    cert.write_text("dummy", encoding="utf-8")
    captured: dict[str, object] = {}

    class DummyClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def __enter__(self):  # pragma: no cover - helper
            return self

        def __exit__(self, exc_type, exc, tb):  # pragma: no cover - helper
            return False

    monkeypatch.setattr("santricity_client.cli.SANtricityClient", DummyClient)

    _build_client(
        base_url="https://array/devmgr/v2",
        auth="basic",
        username="admin",
        password="secret",
        token=None,
        verify_ssl=True,
        cert_path=cert,
        timeout=30.0,
        release_version=None,
        system_id=None,
    )

    assert captured["verify_ssl"] == str(cert)


def test_build_client_rejects_cert_with_no_verify(tmp_path):
    cert = tmp_path / "ca.pem"
    cert.write_text("dummy", encoding="utf-8")

    with pytest.raises(typer.BadParameter):
        _build_client(
            base_url="https://array/devmgr/v2",
            auth="basic",
            username="admin",
            password="secret",
            token=None,
            verify_ssl=False,
            cert_path=cert,
            timeout=30.0,
            release_version=None,
            system_id=None,
        )
