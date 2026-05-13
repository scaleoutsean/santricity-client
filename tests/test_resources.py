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


def test_clone_creation(requests_mock):
    client = build_client(release_version="12.0")
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volume-clones",
        json={"cloneRef": "c1"},
    )

    result = client.clones.create({"sourceRef": "vol1"})

    assert result["cloneRef"] == "c1"


def test_volume_mapping_delete(requests_mock):
    client = build_client(release_version="12.0")
    requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/volume-mappings/map-1",
        json={"deleted": True},
    )

    result = client.mappings.delete("map-1")

    assert result["deleted"] is True


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


def test_system_get_info_selects_active_system(requests_mock):
    client = build_client(base_url="https://array/devmgr/v2", system_id=DEFAULT_SYSTEM_ID)
    requests_mock.get(
        "https://array/devmgr/v2/storage-systems",
        json=[
            {"wwn": "other-system", "chassisSerialNumber": "111"},
            {"wwn": DEFAULT_SYSTEM_ID, "chassisSerialNumber": "952419000943"},
        ],
    )

    info = client.system.get_info()

    assert info["wwn"] == DEFAULT_SYSTEM_ID
    assert info["chassisSerialNumber"] == "952419000943"


def test_system_get_info_falls_back_to_first_entry(requests_mock):
    client = build_client(base_url="https://array/devmgr/v2", system_id=DEFAULT_SYSTEM_ID)
    requests_mock.get(
        "https://array/devmgr/v2/storage-systems",
        json=[
            {"wwn": "unrelated", "chassisSerialNumber": "abc"},
            {"wwn": "something-else", "chassisSerialNumber": "def"},
        ],
    )

    info = client.system.get_info()

    assert info["wwn"] == "unrelated"
    assert info["chassisSerialNumber"] == "abc"


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

def test_consistency_groups_operations(requests_mock):
    client = build_client()
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups",
        json=[{"id": "cg1"}],
    )
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg1",
        json={"id": "cg1"},
    )
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups",
        json={"id": "cg2"},
    )
    requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg2",
        status_code=204,
    )
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg1/member-volumes",
        json=[{"id": "mv1"}],
    )
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg1/member-volumes",
        json={"id": "mv1"},
    )
    requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg1/member-volumes/mv1",
        status_code=204,
    )
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg1/snapshots",
        json=[{"id": "snap1"}],
    )
    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg1/snapshots",
        json=[{"id": "snap2"}],
    )
    requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/consistency-groups/cg1/snapshots/123",
        status_code=204,
    )

    assert client.consistency_groups.list_groups() == [{"id": "cg1"}]
    assert client.consistency_groups.get_group("cg1") == {"id": "cg1"}
    assert client.consistency_groups.create_group({"name": "test"}) == {"id": "cg2"}
    assert client.consistency_groups.delete_group("cg2") is None
    
    assert client.consistency_groups.list_member_volumes("cg1") == [{"id": "mv1"}]
    assert client.consistency_groups.add_member_volume("cg1", {"volId": "v1"}) == {"id": "mv1"}
    assert client.consistency_groups.remove_member_volume("cg1", "mv1") is None
    
    assert client.consistency_groups.list_snapshots("cg1") == [{"id": "snap1"}]
    assert client.consistency_groups.create_snapshot("cg1") == [{"id": "snap2"}]
    assert client.consistency_groups.delete_snapshot("cg1", 123) is None
