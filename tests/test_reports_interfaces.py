import json
from pathlib import Path

from santricity_client.reports.interfaces_report import _resolve_field_path, hostside_interfaces_report


class _FakeInterfaces:
    def __init__(self, rows):
        self._rows = rows

    def get_system_hostside_interfaces(self):
        return self._rows


class _FakeClient:
    def __init__(self, rows):
        self.interfaces = _FakeInterfaces(rows)

    def request(self, method, path):
        if path == "/controllers":
            return []
        raise RuntimeError(path)


def _load_reference_rows(filename: str) -> list[dict]:
    base = Path(__file__).resolve().parent.parent / "references" / "santricity-interfaces-hostside"
    return json.loads((base / filename).read_text())


def test_hostside_interfaces_report_extracts_roce_command_properties():
    rows = _load_reference_rows("example-EF600-GET-interfaces_hostside_NVMe_RoCE_192.168.x.y.json")

    result = hostside_interfaces_report(_FakeClient(rows), protocol="ethernet")

    ready_rows = [row for row in result if row.get("is_command_ipv4_ready") is True]
    blocked_rows = [row for row in result if row.get("is_command_ipv4_ready") is False]

    assert ready_rows
    assert blocked_rows
    assert ready_rows[0]["protocol"] == "ethernet"
    assert ready_rows[0]["transport"] == "ethernet"
    assert ready_rows[0]["command_provider"] == "provider_roce_v2"
    assert ready_rows[0]["command_protocol"] == "nvme"
    assert ready_rows[0]["is_roce_v2_ipv4_enabled"] is True
    assert ready_rows[0]["command_ipv4_address"] == ready_rows[0]["roce_v2_ipv4_address"]
    assert blocked_rows[0]["is_roce_v2_ipv4_enabled"] is False


def test_hostside_interfaces_report_extracts_ib_command_readiness():
    rows = _load_reference_rows("ef80-ib_response_1772376962813.json")

    result = hostside_interfaces_report(_FakeClient(rows), protocol="ib")

    configured_rows = [row for row in result if row.get("infiniband_ipv4_config_state") == "configured"]
    unconfigured_rows = [row for row in result if row.get("infiniband_ipv4_config_state") == "unconfigured"]

    assert configured_rows
    assert unconfigured_rows
    assert configured_rows[0]["command_provider"] == "provider_infiniband"
    assert configured_rows[0]["command_protocol"] == "nvme"
    assert configured_rows[0]["is_command_ipv4_ready"] is True
    assert configured_rows[0]["command_ipv4_address"] == configured_rows[0]["infiniband_ipv4_address"]
    assert unconfigured_rows[0]["is_command_ipv4_ready"] is False


def test_hostside_interfaces_report_keeps_row_when_command_protocol_entry_is_missing():
    rows = [
        {
            "interfaceRef": "iface-1",
            "channelType": "hostside",
            "controllerRef": "ctrl-a-ref",
            "ioInterfaceTypeData": {
                "interfaceType": "ethernet",
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
                "fibre": None,
                "ib": None,
                "iscsi": None,
                "pcie": None,
            },
            "commandProtocolPropertiesList": {"commandProtocolProperties": []},
        }
    ]

    result = hostside_interfaces_report(_FakeClient(rows), protocol="ethernet")

    assert len(result) == 1
    assert result[0]["interface_id"] == "eth-1"
    assert "command_provider" not in result[0]
    assert "is_command_ipv4_ready" not in result[0]


def test_resolve_field_path_returns_none_for_malformed_or_missing_indexed_parts():
    data = {
        "commandProtocolPropertiesList": {
            "commandProtocolProperties": [],
        }
    }

    assert _resolve_field_path(
        data,
        "commandProtocolPropertiesList_commandProtocolProperties[0]_commandProtocol",
    ) is None
    assert _resolve_field_path(
        data,
        "commandProtocolPropertiesList_commandProtocolProperties[]_commandProtocol",
    ) is None