from santricity_client import SANtricityClient
from santricity_client.auth.basic import BasicAuth


def make_client():
    return SANtricityClient(
        base_url="http://example",
        auth_strategy=BasicAuth(username="u", password="p"),
        verify_ssl=True,
        timeout=1.0,
    )


def test_mappings_report_resolves_names_and_pools():
    client = make_client()

    # Minimal, hard-coded fixtures for volumes, pools, hosts, host-groups, mappings
    volumes = [
        {
            "name": "test_name_1",
            "capacity": 10000000,
            "volumeRef": "1111111111111111111111111111111111111111",
            "volumeGroupRef": "2222222222222222222222222222222222222222",
            "id": "1111111111111111111111111111111111111111",
        }
    ]

    pools = [
        {
            "id": "2222222222222222222222222222222222222222",
            "volumeGroupName": "pool-a",
            "freeSpace": 5000000,
            "raidLevel": "raid6",
        }
    ]

    hosts = [
        {
            "hostRef": "3333333333333333333333333333333333333333",
            "hostName": "host-a",
            "id": "3333333333333333333333333333333333333333",
        },
        {
            "hostRef": "5555555555555555555555555555555555555555",
            "label": "host-b",
            "id": "5555555555555555555555555555555555555555",
        },
    ]

    host_groups = [
        {
            "clusterRef": "4444444444444444444444444444444444444444",
            "hostGroupLabel": "host-group-a",
            "id": "4444444444444444444444444444444444444444",
        }
    ]

    mappings = [
        {
            "lunMappingRef": "m1",
            "lun": 1,
            "ssid": 0,
            "perms": 15,
            "volumeRef": "1111111111111111111111111111111111111111",
            "type": "cluster",
            "mapRef": "8500",
            "id": "m1",
            "targetId": "3333333333333333333333333333333333333333",
        },
        {
            "lunMappingRef": "m2",
            "lun": 2,
            "ssid": 1,
            "perms": 15,
            "volumeRef": "1111111111111111111111111111111111111111",
            "type": "cluster",
            "mapRef": "8501",
            "id": "m2",
            "targetId": "4444444444444444444444444444444444444444",
        },
        {
            "lunMappingRef": "m3",
            "lun": 3,
            "ssid": 2,
            "perms": 15,
            "volumeRef": "1111111111111111111111111111111111111111",
            "type": "host",
            "mapRef": "5555555555555555555555555555555555555555",
            "id": "m3",
        },
    ]

    # Patch client resources to return our fixtures
    client.volumes.list = lambda: volumes
    client.pools.list = lambda: pools
    client.hosts.list = lambda: hosts
    client.hosts.list_groups = lambda: host_groups
    client.mappings.list = lambda: mappings

    report = client.mappings_report()

    assert isinstance(report, list)
    assert len(report) == 3

    first = report[0]
    assert first.get("mappableObjectName") == "test_name_1"
    assert first.get("capacity") == 10000000
    assert first.get("poolName") == "pool-a"
    assert first.get("poolFreeSpace") == 5000000
    assert first.get("hostLabel") == "host-a"
    assert first.get("mappingRef") == "8500"

    second = report[1]
    assert second.get("targetLabel") == "host-group-a"
    assert second.get("mappingRef") == "8501"

    third = report[2]
    assert third.get("hostLabel") == "host-b"
    assert third.get("targetLabel") == "host-b"
    assert third.get("mappingRef") == "5555555555555555555555555555555555555555"
