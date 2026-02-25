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


def test_add_initiator_iscsi_default(requests_mock):
    client = build_client()
    host_ref = "host1"
    iqn = "iqn.2010-01.com.example:123"

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts/{host_ref}/initiators",
        json={"id": "init1"},
        additional_matcher=lambda request: request.json() == {"type": "iscsi", "port": iqn},
    )

    result = client.hosts.add_initiator(host_ref, iqn)
    assert result["id"] == "init1"


def test_add_initiator_iscsi_with_chap(requests_mock):
    client = build_client()
    host_ref = "host1"
    iqn = "iqn.2010-01.com.example:123"
    secret = "sosecret"

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts/{host_ref}/initiators",
        json={"id": "init1"},
        additional_matcher=lambda request: request.json()
        == {"type": "iscsi", "port": iqn, "iscsiChapSecret": secret},
    )

    result = client.hosts.add_initiator(host_ref, iqn, chap_secret=secret)
    assert result["id"] == "init1"


def test_add_initiator_nvme(requests_mock):
    client = build_client()
    host_ref = "host1"
    nqn = "nqn.2014-08.org.nvmexpress:uuid:f4a33812-daa8-11e9-9399-3a68dd160bef"

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts/{host_ref}/initiators",
        json={"id": "init1"},
        additional_matcher=lambda request: request.json()
        == {"type": "nvmeof", "port": nqn, "label": "my-nvme"},
    )

    result = client.hosts.add_initiator(host_ref, nqn, type="nvmeof", label="my-nvme")
    assert result["id"] == "init1"


def test_create_host_linux_nvme(requests_mock):
    client = build_client()
    name = "h3"
    port = "nqn.2014-08.org.nvmexpress:uuid:b6087fac-aef6-4e75-85c1-abd7078c94f9"
    port_type = "nvmeof"

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts",
        json={"id": "host-h3", "name": name},
        additional_matcher=lambda request: request.json()
        == {
            "name": name,
            "hostType": {"index": 28},
            "ports": [
                {
                    "label": f"{name}_1",
                    "port": port,
                    "type": port_type,
                }
            ],
        },
    )

    result = client.hosts.create(name, port=port, port_type=port_type)
    assert result["id"] == "host-h3"
    assert result["name"] == name


def test_create_host_with_chap(requests_mock):
    client = build_client()
    name = "host-chap"
    port = "iqn.2023-01.com.example:123"
    port_type = "iscsi"
    chap_secret = "testtesttest"

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts",
        json={"id": "host-chap-id", "name": name},
        additional_matcher=lambda request: request.json()
        == {
            "name": name,
            "hostType": {"index": 28},
            "ports": [
                {
                    "label": f"{name}_1",
                    "port": port,
                    "type": port_type,
                    "iscsiChapSecret": chap_secret,
                }
            ],
        },
    )

    result = client.hosts.create(
        name, port=port, port_type=port_type, iscsi_chap_secret=chap_secret
    )
    assert result["id"] == "host-chap-id"


def test_create_host_group(requests_mock):
    client = build_client()
    name = "beegfs_group"
    hosts = ["host1-ref", "host2-ref"]

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/host-groups",
        json={"id": "group1", "name": name},
        additional_matcher=lambda request: request.json() == {"name": name, "hosts": hosts},
    )

    result = client.hosts.create_group(name, hosts=hosts)
    assert result["id"] == "group1"
    assert result["name"] == name


def test_create_host_fc(requests_mock):
    client = build_client()
    name = "fc-host"
    wwpn = "21:00:00:24:ff:01:02:03"
    port_type = "fc"

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts",
        json={"id": "host-fc", "name": name},
        additional_matcher=lambda request: request.json()
        == {
            "name": name,
            "hostType": {"index": 28},
            "ports": [
                {
                    "label": f"{name}_1",
                    "port": wwpn,
                    "type": port_type,
                }
            ],
        },
    )

    result = client.hosts.create(name, port=wwpn, port_type=port_type)
    assert result["id"] == "host-fc"
    assert result["name"] == name


def test_get_host_by_wwn(requests_mock):
    client = build_client()
    wwpn = "21:00:00:24:ff:01:02:03"
    host_data = {
        "id": "host-fc-id",
        "name": "fc-host",
        "initiators": [{"nodeName": {"remoteNodeWWN": wwpn}}],
    }

    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts", json=[host_data]
    )

    result = client.hosts.get_by_identifiers(wwpn)
    assert result["id"] == "host-fc-id"
    assert result["name"] == "fc-host"


def test_update_host(requests_mock):
    client = build_client()
    host_ref = "host1"
    new_name = "better-host"

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts/{host_ref}",
        json={"id": host_ref, "name": new_name},
        additional_matcher=lambda request: request.json() == {"name": new_name},
    )

    result = client.hosts.update(host_ref, name=new_name)
    assert result["name"] == new_name


def test_update_host_group(requests_mock):
    client = build_client()
    group_ref = "group1"
    new_hosts = ["host3"]

    requests_mock.post(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/host-groups/{group_ref}",
        json={"id": group_ref, "hosts": new_hosts},
        additional_matcher=lambda request: request.json() == {"hosts": new_hosts},
    )

    result = client.hosts.update_group(group_ref, hosts=new_hosts)
    assert result["hosts"] == new_hosts


def test_delete_host(requests_mock):
    client = build_client()
    host_id = "84000000600A098000F63714003037FC695975DD"

    adapter = requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts/{host_id}",
        status_code=204,
    )

    client.hosts.delete(host_id)
    assert adapter.called


def test_delete_group_force(requests_mock):
    client = build_client()
    group_id = "group1"

    adapter = requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/host-groups/{group_id}",
        status_code=204,
    )

    client.hosts.delete_group(group_id, force=True)
    assert adapter.called


def test_delete_group_empty_noforce(requests_mock):
    client = build_client()
    group_id = "group1"

    # Mock list hosts to return empty list
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts",
        json=[],
    )
    adapter = requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/host-groups/{group_id}",
        status_code=204,
    )

    client.hosts.delete_group(group_id, force=False)
    assert adapter.called


def test_delete_group_not_empty_fails(requests_mock):
    import pytest

    from santricity_client.exceptions import RequestError

    client = build_client()
    group_id = "group1"
    host_in_group = {"hostRef": "h1", "clusterRef": group_id, "label": "h1-label"}

    # Mock list hosts to return one host in this group
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts",
        json=[host_in_group],
    )
    adapter = requests_mock.delete(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/host-groups/{group_id}",
        status_code=204,
    )

    with pytest.raises(RequestError) as excinfo:
        client.hosts.delete_group(group_id, force=False)

    assert f"Host group {group_id} is not empty" in str(excinfo.value)
    assert not adapter.called


def test_get_host_by_identifiers(requests_mock):
    client = build_client()
    host_id = "84000000600A098000E3C1B000302F0C650C2668"
    iqn = "iqn.2004-10.com.ubuntu:01:e7f6625b59c"
    wwn = "21:00:00:24:ff:51:2e:5c"
    host_label = "Ubuntu_2204"

    host_data = {
        "hostRef": host_id,
        "id": host_id,
        "label": host_label,
        "name": host_label,
        "hostSidePorts": [
            {
                "address": iqn,
                "label": f"{host_label}_1",
            }
        ],
        "initiators": [
            {
                "nodeName": {
                    "remoteNodeWWN": wwn,
                }
            }
        ],
    }

    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts",
        json=[host_data],
    )

    # Test by ID
    assert client.hosts.get_by_identifiers(host_id)["id"] == host_id
    # Test by label
    assert client.hosts.get_host_by_name(host_label)["id"] == host_id
    # Test by port (address)
    assert client.hosts.get_host_by_host_identifiers(iqn)["id"] == host_id
    # Test by WWN
    assert client.hosts.get_host_by_host_identifiers(wwn)["id"] == host_id
    # Test by name alias
    assert client.hosts.get_by_name(host_label)["id"] == host_id


def test_get_mapping_target(requests_mock):
    client = build_client()
    group_id = "group1"
    host_id = "host1"
    host_data = {
        "id": host_id,
        "label": "host-in-group",
        "clusterRef": group_id,
    }
    group_data = {
        "id": group_id,
        "label": "group1-label",
    }

    # Mock list hosts and get group
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/hosts",
        json=[host_data],
    )
    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/host-groups/{group_id}",
        json=group_data,
    )

    # Calling target on host ID should return the GROUP
    result = client.hosts.get_mapping_target(host_id)
    assert result["id"] == group_id
    assert result["label"] == "group1-label"
