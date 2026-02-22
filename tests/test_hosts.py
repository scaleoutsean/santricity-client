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
