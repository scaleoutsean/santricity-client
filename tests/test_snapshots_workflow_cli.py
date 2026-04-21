import json

from typer.testing import CliRunner

from santricity_client.cli import app

runner = CliRunner()
SYSTEM_ID = "600A098000F63714"


def test_clean_slate_plan_repo_group_does_not_create_snapshot_objects(requests_mock):
    base_url = "https://array/devmgr/v2"

    # Clean-slate list endpoints start empty.
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-schedules",
        json=[],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat",
        json=[],
    )

    # Planning requires resolving the base volume and requesting candidates.
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"label": "vol1", "volumeRef": "vol-ref-1"}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat/single",
        json=[{"baseMappableObjectId": "vol-ref-1", "candidate": {"candType": "newVol"}}],
    )

    plan_result = runner.invoke(
        app,
        [
            "snapshots",
            "plan-repo-group",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
            "--volume",
            "vol1",
            "--percent-capacity",
            "10",
        ],
    )

    assert plan_result.exit_code == 0
    plan_payload = json.loads(plan_result.stdout)
    assert plan_payload[0]["baseMappableObjectId"] == "vol-ref-1"
    assert plan_payload[0]["candidate"]["candType"] == "newVol"

    groups_result = runner.invoke(
        app,
        [
            "snapshots",
            "list-groups",
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
    repos_result = runner.invoke(
        app,
        [
            "snapshots",
            "list-repo-groups",
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

    assert groups_result.exit_code == 0
    assert repos_result.exit_code == 0
    assert json.loads(groups_result.stdout) == []
    assert json.loads(repos_result.stdout) == []
