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
    """Test discovering NVMe portals from interfaces when target-settings is empty."""
    client = build_client()
    nqn = "nqn.1992-08.com.netapp:5700.600a0b8000000000"
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/nvmeof/target-settings",
        json={"targetRef": "test-nvme-target", "nodeName": {"nvmeNodeName": nqn}, "portals": []},
    )

    # EF600 style interface listing
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/interfaces",
        json=[
            {
                "interfaceRef": "interface-1",
                "commandProtocolPropertiesList": {
                    "commandProtocolProperties": [
                        {
                            "commandProtocol": "nvme",
                            "nvmeProperties": {
                                "nvmeofProperties": {
                                    "roceV2Properties": {
                                        "ipAddressData": {
                                            "ipv4Data": {"ipv4Address": "192.168.10.101"}
                                        },
                                        "listeningPort": 4420,
                                    }
                                }
                            },
                        }
                    ]
                },
            },
            {
                "interfaceRef": "interface-2",
                "commandProtocolPropertiesList": {
                    "commandProtocolProperties": [
                        {
                            "commandProtocol": "nvme",
                            "nvmeProperties": {
                                "nvmeofProperties": {
                                    "ibProperties": {
                                        "ipAddressData": {
                                            "ipv4Data": {"ipv4Address": "192.168.10.102"}
                                        },
                                        "listeningPort": 4421,
                                    }
                                }
                            },
                        }
                    ]
                },
            },
        ],
    )

    result = client.interfaces.get_nvme_target_settings()
    assert result["nodeName"]["nvmeNodeName"] == nqn
    assert len(result["portals"]) == 2
    addresses = [p["address"] for p in result["portals"]]
    assert "192.168.10.101" in addresses
    assert "192.168.10.102" in addresses
    ports = [p["port"] for p in result["portals"]]
    assert 4420 in ports
    assert 4421 in ports
