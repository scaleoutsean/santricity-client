from santricity_client.reports.controllers import controllers_report


class _FakeInterfaces:
    def __init__(self, rows):
        self._rows = rows

    def get_system_hostside_interfaces(self):
        return self._rows


class _FakeClient:
    def __init__(self, interface_rows, controller_rows):
        self.interfaces = _FakeInterfaces(interface_rows)
        self._controller_rows = controller_rows

    def request(self, method, path):
        if path == "/controllers":
            return self._controller_rows
        raise RuntimeError(path)


def test_controllers_report_embeds_interface_contract_fields():
    interface_rows = [
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
    ]
    controller_rows = [
        {
            "id": "ctrl-a",
            "controllerRef": "ctrl-a-ref",
            "modelName": "EF600",
            "status": "optimal",
            "physicalLocation": {"label": "A"},
        }
    ]

    result = controllers_report(_FakeClient(interface_rows, controller_rows))

    assert len(result) == 1
    controller = result[0]
    assert controller["hostside_interface_count"] == 1
    assert len(controller["hostside_interfaces"]) == 1

    embedded = controller["hostside_interfaces"][0]
    expected_fields = {
        "controller_id",
        "controller_label",
        "controller_ref",
        "channel",
        "channel_port_ref",
        "command_ipv4_address",
        "command_protocol",
        "command_provider",
        "current_interface_speed_mebibits_per_second",
        "id",
        "interface_id",
        "is_command_ipv4_ready",
        "is_roce_v2_ipv4_enabled",
        "link_status",
        "maximum_interface_speed_mebibits_per_second",
        "maximum_mtu_bytes",
        "protocol",
        "roce_v2_ipv4_address",
        "transport",
    }

    assert expected_fields.issubset(embedded.keys())
    assert embedded["protocol"] == "ethernet"
    assert embedded["transport"] == "ethernet"
    assert embedded["command_provider"] == "provider_roce_v2"
    assert embedded["command_protocol"] == "nvme"
    assert embedded["command_ipv4_address"] == "192.168.2.10"
    assert embedded["is_command_ipv4_ready"] is True


def test_controllers_report_embeds_ib_interface_contract_fields():
    interface_rows = [
        {
            "interfaceRef": "iface-2",
            "channelType": "hostside",
            "controllerRef": "ctrl-b-ref",
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
                    "supportedSpeed": ["speed100gig", "speed200gig"],
                    "currentLinkWidth": "width4x",
                    "supportedLinkWidth": ["width4x"],
                    "currentDataVirtualLanes": 4,
                    "maximumDataVirtualLanes": 4,
                    "isNVMeSupported": True,
                    "controllerId": "ctrl-b",
                    "addressId": "FE8000000000000B00A09800006AAF18",
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
                                            "configState": "configured",
                                            "ipv4Address": "192.168.3.100",
                                            "ipv4SubnetMask": "255.255.255.0",
                                            "ipv4GatewayAddress": "0.0.0.0",
                                        },
                                        "ipv6Data": None,
                                    },
                                    "listeningPort": 4420,
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
        }
    ]
    controller_rows = [
        {
            "id": "ctrl-b",
            "controllerRef": "ctrl-b-ref",
            "modelName": "EF600",
            "status": "optimal",
            "physicalLocation": {"label": "B"},
        }
    ]

    result = controllers_report(_FakeClient(interface_rows, controller_rows))

    assert len(result) == 1
    controller = result[0]
    assert controller["hostside_interface_count"] == 1
    assert len(controller["hostside_interfaces"]) == 1

    embedded = controller["hostside_interfaces"][0]
    expected_fields = {
        "address_id",
        "channel",
        "channel_port_ref",
        "command_ipv4_address",
        "command_protocol",
        "command_provider",
        "controller_id",
        "controller_label",
        "controller_ref",
        "current_data_virtual_lane_count",
        "current_interface_speed_mebibits_per_second",
        "current_link_width",
        "id",
        "infiniband_ipv4_address",
        "infiniband_ipv4_config_state",
        "interface_id",
        "is_command_ipv4_ready",
        "is_nvme_supported",
        "link_state",
        "maximum_data_virtual_lane_count",
        "maximum_mtu_bytes",
        "port_state",
        "protocol",
        "supported_link_widths_list",
        "supported_speeds_mebibits_per_second_list",
        "transport",
    }

    assert expected_fields.issubset(embedded.keys())
    assert embedded["protocol"] == "ib"
    assert embedded["transport"] == "ib"
    assert embedded["command_provider"] == "provider_infiniband"
    assert embedded["command_protocol"] == "nvme"
    assert embedded["infiniband_ipv4_config_state"] == "configured"
    assert embedded["command_ipv4_address"] == embedded["infiniband_ipv4_address"]
    assert embedded["command_ipv4_address"] == "192.168.3.100"
    assert embedded["is_command_ipv4_ready"] is True