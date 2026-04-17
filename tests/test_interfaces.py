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


def test_get_iscsi_target_settings(requests_mock):
    client = build_client()
    target_data = {
        "targetRef": "90000000600A098000F63714003321185E79C180",
        "nodeName": {
            "ioInterfaceType": "iscsi",
            "iscsiNodeName": "iqn.1992-08.com.netapp:5700.600a098000f63714000000005e79c17c",
        },
        "portals": [
            {
                "ipAddress": {"ipv4Address": "192.168.130.102"},
                "tcpListenPort": 3260,
            }
        ],
    }

    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/iscsi/target-settings",
        json=target_data,
    )

    result = client.interfaces.get_iscsi_target_settings()
    assert (
        result["nodeName"]["iscsiNodeName"]
        == "iqn.1992-08.com.netapp:5700.600a098000f63714000000005e79c17c"
    )
    assert result["portals"][0]["ipAddress"]["ipv4Address"] == "192.168.130.102"


def test_get_nvme_target_settings_with_interface_discovery(requests_mock):
    """NVMe target settings are returned directly from initiator-settings."""
    client = build_client()
    nqn = "nqn.1992-08.com.netapp:5700.600a0b8000000000"
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/nvmeof/initiator-settings",
        json={"targetRef": "test-nvme-target", "nodeName": {"nvmeNodeName": nqn}, "portals": []},
    )

    result = client.interfaces.get_nvme_target_settings()
    assert result["nodeName"]["nvmeNodeName"] == nqn
    assert result["portals"] == []


def test_get_system_hostside_interfaces_filters_non_hostside(requests_mock):
    client = build_client()
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/interfaces",
        json=[
            {"interfaceRef": "host-1", "channelType": "hostside"},
            {"interfaceRef": "host-2", "channelType": "hostside"},
            {"interfaceRef": "driveside-1", "channelType": "driveside"},
        ],
    )

    result = client.interfaces.get_system_hostside_interfaces()

    refs = [item["interfaceRef"] for item in result]
    assert refs == ["host-1", "host-2"]


