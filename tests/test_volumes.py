import pytest

from santricity_client import SANtricityClient
from santricity_client.auth.basic import BasicAuth

DEFAULT_SYSTEM_ID = "600A098000F63714"


def build_client(
    *,
    release_version: str | None = None,
    base_url: str = "https://array/devmgr/v2",
    system_id: str | None = DEFAULT_SYSTEM_ID,
):
    return SANtricityClient(
        base_url=base_url,
        auth_strategy=BasicAuth("u", "p"),
        release_version=release_version,
        system_id=system_id,
    )


def test_expand_volume_bytes(requests_mock):
    client = build_client()
    volume_ref = "vol1"
    new_size = 10737418240  # 10 GiB in bytes

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volumes/{volume_ref}/expand",
        json={"percentComplete": 0, "timeToCompletion": 0, "action": "none"},
        additional_matcher=lambda request: request.json()
        == {"expansionSize": new_size, "sizeUnit": "bytes"},
    )

    result = client.volumes.expand(volume_ref, new_size)
    assert result["percentComplete"] == 0


def test_expand_volume_gb_decimal(requests_mock):
    client = build_client()
    volume_ref = "vol1"
    size_gb = 10
    expected_bytes = 10 * (1000**3)

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volumes/{volume_ref}/expand",
        json={"percentComplete": 0},
        additional_matcher=lambda request: request.json()
        == {"expansionSize": expected_bytes, "sizeUnit": "bytes"},
    )

    client.volumes.expand(volume_ref, size_gb, unit="gb")


def test_expand_volume_gib_binary(requests_mock):
    client = build_client()
    volume_ref = "vol1"
    size_gib = 10
    expected_bytes = 10 * (1024**3)

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volumes/{volume_ref}/expand",
        json={"percentComplete": 0},
        additional_matcher=lambda request: request.json()
        == {"expansionSize": expected_bytes, "sizeUnit": "bytes"},
    )

    client.volumes.expand(volume_ref, size_gib, unit="gib")


def test_expand_volume_invalid_unit():
    client = build_client()
    with pytest.raises(ValueError, match="Invalid unit: bad_unit"):
        client.volumes.expand("vol1", 100, unit="bad_unit")
