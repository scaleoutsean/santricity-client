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


def test_get_pool_by_name(requests_mock):
    client = build_client()
    pool_data = [
        {"id": "pool1", "label": "Gold-Pool", "name": "Gold-Pool"},
        {"id": "pool2", "label": "Silver-Pool", "name": "Silver-Pool"},
    ]

    requests_mock.get(
        f"https://array/devmgr/v2/storage-systems/{DEFAULT_SYSTEM_ID}/storage-pools",
        json=pool_data,
    )

    # Find by label
    result = client.pools.get_by_name("Gold-Pool")
    assert result["id"] == "pool1"

    # Not found
    result = client.pools.get_by_name("Non-Existent")
    assert result is None
