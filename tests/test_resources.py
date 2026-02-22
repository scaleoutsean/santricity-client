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


def test_create_volume_mapping(requests_mock):
    client = build_client(release_version="11.90")
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volume-mappings",
        json={"id": "map1"},
    )

    result = client.mappings.create({"volumeRef": "1", "lun": 0})

    assert result["id"] == "map1"


def test_volume_mapping_fallback_to_legacy_endpoint(requests_mock):
    client = build_client(release_version="12.0")
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/v2/volume-mappings",
        status_code=404,
        json={"error": "missing"},
    )
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volume-mappings",
        json={"id": "legacy"},
    )

    result = client.mappings.create({"volumeRef": "2", "lun": 1})

    assert result["id"] == "legacy"


def test_clone_creation_falls_back(requests_mock):
    client = build_client(release_version="12.0")
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/v2/volume-clones",
        status_code=405,
        json={"error": "deprecated"},
    )
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volume-clones",
        json={"cloneRef": "c1"},
    )

    result = client.clones.create({"sourceRef": "vol1"})

    assert result["cloneRef"] == "c1"


def test_system_release_summary_prefers_bundle_display(requests_mock):
    client = build_client(base_url="https://array/devmgr/v2")
    requests_mock.get(
        "https://array/devmgr/v2/firmware/embedded-firmware/1/versions",
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

    summary = client.system.release_summary()

    assert summary["version"] == "11.90R2"
    assert summary["source"] == "bundleDisplay"
    assert summary["symbolApi"] == "v1190api9"


def test_system_release_summary_handles_missing_firmware_endpoint(requests_mock):
    client = build_client(base_url="https://array/devmgr/v2")
    requests_mock.get(
        "https://array/devmgr/v2/firmware/embedded-firmware/1/versions",
        status_code=404,
        json={"message": "missing"},
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

    summary = client.system.release_summary()

    assert summary["version"] == "v1190api9"
    assert summary["source"] == "symbolApi"
    assert summary["bundleDisplay"] is None
    assert summary["errors"]
