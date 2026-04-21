import json

import pytest
import typer
from typer.testing import CliRunner

from santricity_client.cli import _build_client, app

runner = CliRunner()

SYSTEM_ID = "600A098000F63714"


def test_system_version_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/firmware/embedded-firmware/1/versions",
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

    result = runner.invoke(
        app,
        [
            "system",
            "version",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "11.90R2" in result.stdout


def test_pools_list_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools",
        json=[{"label": "poolA"}],
    )

    result = runner.invoke(
        app,
        [
            "pools",
            "list",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "poolA" in result.stdout


def test_pools_list_cli_json_output(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools",
        json=[{"label": "poolA"}],
    )

    result = runner.invoke(
        app,
        [
            "pools",
            "list",
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

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["label"] == "poolA"


def test_reports_interfaces_cli_renders_table(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/interfaces",
        json=[
            {
                "interfaceRef": "iface-1",
                "channelType": "hostside",
                "controllerRef": "ctrl-a-ref",
                "ioInterfaceTypeData": {
                    "interfaceType": "ethernet",
                    "fibre": None,
                    "ib": None,
                    "iscsi": None,
                    "ethernet": {
                        "channel": 1,
                        "channelPortRef": "port-1",
                        "interfaceData": {
                            "type": "ethernet",
                            "ethernetData": {
                                "macAddress": "001122334455",
                                "maximumFramePayloadSize": 9000,
                                "currentInterfaceSpeed": "speed25gig",
                                "maximumInterfaceSpeed": "speed100gig",
                                "linkStatus": "up",
                            },
                        },
                        "controllerId": "ctrl-a",
                        "interfaceId": "eth-1",
                        "addressId": "001122334455",
                        "id": "eth-1",
                    },
                    "pcie": None,
                },
                "commandProtocolPropertiesList": {
                    "commandProtocolProperties": [
                        {
                            "commandProtocol": "nvme",
                            "nvmeProperties": {
                                "commandSet": "nvmeof",
                                "nvmeofProperties": {
                                    "provider": "providerRocev2",
                                    "ibProperties": None,
                                    "roceV2Properties": {
                                        "ipv4Enabled": True,
                                        "ipv4Data": {
                                            "ipv4Address": "192.168.2.10",
                                            "ipv4OutboundPacketPriority": {
                                                "isEnabled": False,
                                                "value": 0,
                                            },
                                        },
                                    },
                                    "fcProperties": None,
                                },
                                "nvmeProperties": None,
                            },
                            "scsiProperties": None,
                        }
                    ]
                },
            }
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/controllers",
        json=[
            {
                "id": "ctrl-a",
                "controllerRef": "ctrl-a-ref",
                "physicalLocation": {"label": "A"},
            }
        ],
    )

    result = runner.invoke(
        app,
        [
            "reports",
            "interfaces",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "Host-side Interfaces" in result.stdout
    assert "eth-1" in result.stdout
    assert "192.1" in result.stdout
    assert "Yes" in result.stdout


def test_reports_controllers_cli_renders_table_with_readiness_summary(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/interfaces",
        json=[
            {
                "interfaceRef": "iface-1",
                "channelType": "hostside",
                "controllerRef": "ctrl-a-ref",
                "ioInterfaceTypeData": {
                    "interfaceType": "ethernet",
                    "fibre": None,
                    "ib": None,
                    "iscsi": None,
                    "ethernet": {
                        "channel": 1,
                        "channelPortRef": "port-1",
                        "interfaceData": {
                            "type": "ethernet",
                            "ethernetData": {
                                "macAddress": "001122334455",
                                "maximumFramePayloadSize": 9000,
                                "currentInterfaceSpeed": "speed25gig",
                                "maximumInterfaceSpeed": "speed100gig",
                                "linkStatus": "up",
                            },
                        },
                        "controllerId": "ctrl-a",
                        "interfaceId": "eth-1",
                        "addressId": "001122334455",
                        "id": "eth-1",
                    },
                    "pcie": None,
                },
                "commandProtocolPropertiesList": {
                    "commandProtocolProperties": [
                        {
                            "commandProtocol": "nvme",
                            "nvmeProperties": {
                                "commandSet": "nvmeof",
                                "nvmeofProperties": {
                                    "provider": "providerRocev2",
                                    "ibProperties": None,
                                    "roceV2Properties": {
                                        "ipv4Enabled": True,
                                        "ipv4Data": {
                                            "ipv4Address": "192.168.2.10",
                                            "ipv4OutboundPacketPriority": {
                                                "isEnabled": False,
                                                "value": 0,
                                            },
                                        },
                                    },
                                    "fcProperties": None,
                                },
                                "nvmeProperties": None,
                            },
                            "scsiProperties": None,
                        }
                    ]
                },
            },
            {
                "interfaceRef": "iface-2",
                "channelType": "hostside",
                "controllerRef": "ctrl-a-ref",
                "ioInterfaceTypeData": {
                    "interfaceType": "ib",
                    "fibre": None,
                    "iscsi": None,
                    "ethernet": None,
                    "ib": {
                        "interfaceId": "ib-1",
                        "channel": 2,
                        "channelPortRef": "port-2",
                        "linkState": "active",
                        "portState": "unknown",
                        "maximumTransmissionUnit": 1500,
                        "currentSpeed": "speed200gig",
                        "supportedSpeed": ["speed200gig"],
                        "currentLinkWidth": "width4x",
                        "supportedLinkWidth": ["width4x"],
                        "currentDataVirtualLanes": 4,
                        "maximumDataVirtualLanes": 4,
                        "isNVMeSupported": True,
                        "controllerId": "ctrl-a",
                        "addressId": "fe80::1",
                        "id": "ib-1",
                    },
                    "pcie": None,
                },
                "commandProtocolPropertiesList": {
                    "commandProtocolProperties": [
                        {
                            "commandProtocol": "nvme",
                            "nvmeProperties": {
                                "commandSet": "nvmeof",
                                "nvmeofProperties": {
                                    "provider": "providerInfiniband",
                                    "ibProperties": {
                                        "ipAddressData": {
                                            "ipv4Data": {
                                                "configState": "unconfigured",
                                                "ipv4Address": "192.168.3.100",
                                            }
                                        }
                                    },
                                    "roceV2Properties": None,
                                    "fcProperties": None,
                                },
                                "nvmeProperties": None,
                            },
                            "scsiProperties": None,
                        }
                    ]
                },
            },
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/controllers",
        json=[
            {
                "id": "ctrl-a",
                "controllerRef": "ctrl-a-ref",
                "modelName": "EF600",
                "status": "optimal",
                "physicalLocation": {"label": "A"},
            }
        ],
    )

    result = runner.invoke(
        app,
        [
            "reports",
            "controllers",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "Controllers" in result.stdout
    assert "EF600" in result.stdout
    assert "2" in result.stdout
    assert "1/2" in result.stdout


def test_snapshots_plan_repo_group_returns_candidates(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"label": "vol1", "volumeRef": "vol-ref-1"}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat/single",
        json=[{"baseMappableObjectId": "vol-ref-1", "candidate": {"candType": "newVol"}}],
    )

    result = runner.invoke(
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

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]["baseMappableObjectId"] == "vol-ref-1"
    assert payload[0]["candidate"]["candType"] == "newVol"


def test_snapshots_create_repo_group_warns_that_it_only_plans(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"label": "vol1", "volumeRef": "vol-ref-1"}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat/single",
        json=[{"baseMappableObjectId": "vol-ref-1", "candidate": {"candType": "newVol"}}],
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "create-repo-group",
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

    assert result.exit_code == 0
    assert "planning alias only" in result.stderr.lower()
    payload = json.loads(result.stdout)
    assert payload[0]["candidate"]["candType"] == "newVol"


def test_snapshots_list_images_warns_and_behaves_like_list_snapshots(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-images",
        json=[
            {
                "pitRef": "pit-1",
                "pitGroupRef": "group-1",
                "id": "pit-1",
                "status": "optimal",
            }
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[{"pitGroupRef": "group-1", "name": "vol1_SG_01"}],
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "list-images",
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

    assert result.exit_code == 0
    assert "legacy alias" in result.stderr.lower()
    payload = json.loads(result.stdout)
    assert payload[0]["snapshotGroupName"] == "vol1_SG_01"


def test_snapshots_delete_group_command(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.delete(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups/group-1",
        status_code=204,
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "delete-group",
            "group-1",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "deleted" in result.stdout.lower()


def test_snapshots_delete_repo_group_explains_limitation():
    result = runner.invoke(app, ["snapshots", "delete-repo-group", "repo-1"])

    assert result.exit_code == 1
    assert "does not expose" in result.stderr.lower()


def test_snapshots_list_repo_volumes_filters_concat_and_free_repository_volumes(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[
            {
                "label": "vol1",
                "volumeRef": "vol-1",
                "volumeUse": "standardVolume",
                "mapped": True,
                "totalSizeInBytes": "10737418240",
                "status": "optimal",
            },
            {
                "label": "repos_0001",
                "volumeRef": "repo-free-1",
                "volumeUse": "freeRepositoryVolume",
                "mapped": False,
                "totalSizeInBytes": "8589934592",
                "status": "optimal",
            },
            {
                "label": "concat_repo_01",
                "volumeRef": "repo-concat-1",
                "volumeUse": "concatVolume",
                "mapped": False,
                "totalSizeInBytes": "17179869184",
                "status": "optimal",
            },
        ],
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "list-repo-volumes",
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

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    refs = {item["volumeRef"] for item in payload}
    assert refs == {"repo-free-1", "repo-concat-1"}


def test_snapshots_list_groups_marks_schedule_owned(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[
            {"pitGroupRef": "group-a", "name": "vol1_SG_01", "snapshotCount": 1},
            {"pitGroupRef": "group-b", "name": "vol1_SG_02", "snapshotCount": 0},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-schedules",
        json=[
            {"schedRef": "sched-1", "targetObject": "group-a"},
            {"schedRef": "sched-2", "targetObject": "group-a"},
        ],
    )

    result = runner.invoke(
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

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    by_ref = {row["pitGroupRef"]: row for row in payload}
    assert by_ref["group-a"]["isScheduleOwned"] is True
    assert by_ref["group-a"]["scheduleCount"] == 2
    assert by_ref["group-b"]["isScheduleOwned"] is False
    assert by_ref["group-b"]["scheduleCount"] == 0


def test_snapshots_list_group_util_marks_schedule_owned(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups/repository-utilization",
        json=[
            {"groupRef": "group-a", "pitGroupBytesUsed": "1024", "pitGroupBytesAvailable": "2048"},
            {"groupRef": "group-b", "pitGroupBytesUsed": "4096", "pitGroupBytesAvailable": "8192"},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[
            {"pitGroupRef": "group-a", "name": "vol1_SG_01"},
            {"pitGroupRef": "group-b", "name": "vol1_SG_02"},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-schedules",
        json=[
            {"schedRef": "sched-1", "targetObject": "group-a"},
        ],
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "list-group-util",
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

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    by_ref = {row["groupRef"]: row for row in payload}
    assert by_ref["group-a"]["snapshotGroupName"] == "vol1_SG_01"
    assert by_ref["group-a"]["isScheduleOwned"] is True
    assert by_ref["group-a"]["scheduleCount"] == 1
    assert by_ref["group-b"]["isScheduleOwned"] is False
    assert by_ref["group-b"]["scheduleCount"] == 0


def test_snapshots_create_snapshot_auto_excludes_schedule_owned_groups(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"label": "vol1", "volumeRef": "vol-ref-1"}],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[
            {"pitGroupRef": "group-sched", "baseVolume": "vol-ref-1", "snapshotCount": 1},
            {"pitGroupRef": "group-free", "baseVolume": "vol-ref-1", "snapshotCount": 1},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-schedules",
        json=[{"schedRef": "sched-1", "targetObject": "group-sched"}],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups/repository-utilization",
        json=[
            {"groupRef": "group-sched", "pitGroupBytesAvailable": "999999"},
            {"groupRef": "group-free", "pitGroupBytesAvailable": "1000"},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat",
        json=[],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-images",
        json={"pitRef": "pit-1", "pitGroupRef": "group-free", "status": "optimal"},
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "create-snapshot",
            "--auto",
            "--volume",
            "vol1",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["pitGroupRef"] == "group-free"
    assert "auto-selected snapshot group 'group-free'" in result.stderr.lower()


def test_snapshots_create_snapshot_auto_fails_when_only_schedule_owned_groups_exist(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"label": "vol1", "volumeRef": "vol-ref-1"}],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[
            {"pitGroupRef": "group-sched", "baseVolume": "vol-ref-1", "snapshotCount": 1},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-schedules",
        json=[{"schedRef": "sched-1", "targetObject": "group-sched"}],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups/repository-utilization",
        json=[
            {"groupRef": "group-sched", "pitGroupBytesAvailable": "999999"},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat",
        json=[],
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "create-snapshot",
            "--auto",
            "--volume",
            "vol1",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 1
    assert "no eligible snapshot group found" in result.stderr.lower()


def test_snapshots_create_snapshot_auto_grows_group_when_none_meet_min_free(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"label": "vol1", "volumeRef": "vol-ref-1"}],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[
            {
                "pitGroupRef": "group-a",
                "baseVolume": "vol-ref-1",
                "snapshotCount": 1,
                "repositoryVolume": "repo-a",
                "maxBaseCapacity": "10737418240",
                "repositoryCapacity": "2147483648",
            },
            {
                "pitGroupRef": "group-b",
                "baseVolume": "vol-ref-1",
                "snapshotCount": 1,
                "repositoryVolume": "repo-b",
                "maxBaseCapacity": "10737418240",
                "repositoryCapacity": "2147483648",
            },
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-schedules",
        json=[],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups/repository-utilization",
        json=[
            {"groupRef": "group-a", "pitGroupBytesAvailable": "536870912", "pitGroupBytesUsed": "1610612736"},
            {"groupRef": "group-b", "pitGroupBytesAvailable": "214748364", "pitGroupBytesUsed": "1932735284"},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat",
        json=[
            {"id": "repo-a", "memberCount": 2},
            {"id": "repo-b", "memberCount": 1},
        ],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat/single",
        json=[{"baseMappableObjectId": "vol-ref-1", "candidate": {"candType": "newVol", "volumeGroupId": "0"}}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat/repo-a/expand",
        json={"id": "repo-a", "memberCount": 3},
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-images",
        json={"pitRef": "pit-1", "pitGroupRef": "group-a", "status": "optimal"},
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "create-snapshot",
            "--auto",
            "--volume",
            "vol1",
            "--min-free-percent",
            "10",
            "--growth-step-percent",
            "10",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["pitGroupRef"] == "group-a"
    assert "expanded repository 'repo-a' by 10%" in result.stderr.lower()


def test_snapshots_create_snapshot_auto_min_free_fails_without_growth(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"label": "vol1", "volumeRef": "vol-ref-1"}],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups",
        json=[
            {
                "pitGroupRef": "group-a",
                "baseVolume": "vol-ref-1",
                "snapshotCount": 1,
                "repositoryVolume": "repo-a",
                "maxBaseCapacity": "10737418240",
                "repositoryCapacity": "2147483648",
            },
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-schedules",
        json=[],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/snapshot-groups/repository-utilization",
        json=[
            {"groupRef": "group-a", "pitGroupBytesAvailable": "536870912", "pitGroupBytesUsed": "1610612736"},
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/repositories/concat",
        json=[
            {"id": "repo-a", "memberCount": 2},
        ],
    )

    result = runner.invoke(
        app,
        [
            "snapshots",
            "create-snapshot",
            "--auto",
            "--volume",
            "vol1",
            "--min-free-percent",
            "10",
            "--no-auto-grow-if-needed",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 1
    assert "no eligible snapshot group found" in result.stderr.lower()


def test_volumes_create_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "0400" in result.stdout
    payload = requests_mock.last_request.json()
    assert payload["poolId"] == "0400"
    assert payload["name"] == "demo"


def test_volumes_check_names_cli_detects_duplicates(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[
            {"name": "db", "volumeRef": "1"},
            {"name": "db", "volumeRef": "2"},
            {"name": "logs", "volumeRef": "3"},
        ],
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "check-names",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 1
    assert "duplicate" in result.stderr.lower()


def test_volumes_check_names_cli_unique(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[
            {"name": "db", "volumeRef": "1"},
            {"name": "logs", "volumeRef": "2"},
        ],
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "check-names",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "unique" in result.stdout.lower()


def test_volumes_create_cli_blocks_duplicate_names(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[{"name": "demo", "volumeRef": "1"}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 1
    assert requests_mock.call_count == 1  # only the /volumes GET should fire


def test_volumes_create_cli_allows_duplicate_when_overridden(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--allow-duplicate-name",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0


def test_volumes_create_cli_fallbacks_to_legacy_endpoint(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json=[],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/storage-pools/0400/volumes",
        status_code=404,
        json={"message": "missing"},
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volumes",
        json={"volumeRef": "0400", "name": "demo"},
    )

    result = runner.invoke(
        app,
        [
            "volumes",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--pool-id",
            "0400",
            "--name",
            "demo",
            "--size",
            "10",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert requests_mock.call_count == 3


def test_mappings_list_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volume-mappings",
        json=[{"mappingRef": "m1"}],
    )

    result = runner.invoke(
        app,
        [
            "mappings",
            "list",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "m1" in result.stdout


def test_mappings_create_cli_with_host_resolution(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/hosts",
        json=[{"label": "apphost", "hostRef": "hostRef01"}],
    )
    requests_mock.post(
        f"{base_url}/storage-systems/{SYSTEM_ID}/volume-mappings",
        json={"mappingRef": "map1"},
    )

    result = runner.invoke(
        app,
        [
            "mappings",
            "create",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--volume-ref",
            "vol1",
            "--host",
            "apphost",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "map1" in result.stdout
    payload = requests_mock.request_history[-1].json()
    assert payload["mappableObjectId"] == "vol1"
    assert payload["targetId"] == "hostRef01"


def test_hosts_membership_cli(requests_mock):
    base_url = "https://array/devmgr/v2"
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/hosts",
        json=[
            {
                "label": "app1",
                "hostRef": "hostRef01",
                "clusterRef": "cluster01",
            }
        ],
    )
    requests_mock.get(
        f"{base_url}/storage-systems/{SYSTEM_ID}/host-groups",
        json=[{"label": "prod-cluster", "clusterRef": "cluster01"}],
    )

    result = runner.invoke(
        app,
        [
            "hosts",
            "membership",
            "--base-url",
            base_url,
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            SYSTEM_ID,
        ],
    )

    assert result.exit_code == 0
    assert "prod-cluster" in result.stdout


def test_build_client_accepts_cert_path(monkeypatch, tmp_path):
    cert = tmp_path / "ca.pem"
    cert.write_text("dummy", encoding="utf-8")
    captured: dict[str, object] = {}

    class DummyClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def __enter__(self):  # pragma: no cover - helper
            return self

        def __exit__(self, exc_type, exc, tb):  # pragma: no cover - helper
            return False

    monkeypatch.setattr("santricity_client.cli.SANtricityClient", DummyClient)

    _build_client(
        base_url="https://array/devmgr/v2",
        auth="basic",
        username="admin",
        password="secret",
        token=None,
        verify_ssl=True,
        cert_path=cert,
        timeout=30.0,
        release_version=None,
        system_id=None,
    )

    assert captured["verify_ssl"] == str(cert)


def test_build_client_rejects_cert_with_no_verify(tmp_path):
    cert = tmp_path / "ca.pem"
    cert.write_text("dummy", encoding="utf-8")

    with pytest.raises(typer.BadParameter):
        _build_client(
            base_url="https://array/devmgr/v2",
            auth="basic",
            username="admin",
            password="secret",
            token=None,
            verify_ssl=False,
            cert_path=cert,
            timeout=30.0,
            release_version=None,
            system_id=None,
        )
