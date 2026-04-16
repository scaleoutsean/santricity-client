"""Interface module."""

from __future__ import annotations

from typing import Any

from .base import ResourceBase


class InterfacesResource(ResourceBase):
    """Access controller interface metadata."""

    def list(self) -> list[dict[str, Any]]:
        return self._get("/interfaces")

    def get(self, interface_id: str) -> dict[str, Any]:
        return self._get(f"/interfaces/{interface_id}")

    def get_iscsi_target_settings(self) -> dict[str, Any]:
        """Get iSCSI target settings, including the target IQN and portals.

        Returns:
            A dictionary containing targetRef, nodeName (IQN), and portals list.
        """
        return self._get("/iscsi/target-settings")

    def get_nvme_target_settings(self) -> dict[str, Any]:
        """Get NVMeoF target settings, including the target NQN and portals.

        The preferred endpoint is `/nvmeof/initiator-settings` on modern
        arrays, with fallback to `/nvmeof/target-settings` for compatibility.
        If the endpoint does not return portals, this method attempts to
        discover portals by querying the controller interfaces.

        Returns:
            A dictionary containing targetRef, nodeName (NQN), and portals list.
        """
        settings = self._request_with_fallback(
            "GET",
            "/nvmeof/initiator-settings",
            fallback_path="/nvmeof/target-settings",
        )
        if not settings.get("portals"):
            # Discover portals from interfaces
            portals = []
            for interface in self.list():
                # EF600 specific check (based on structure in
                # references/example-EF600-GET-interfaces.json)
                proto_list = interface.get("commandProtocolPropertiesList", {}) or {}
                proto_props = proto_list.get("commandProtocolProperties", []) or []
                for prop in proto_props:
                    if prop.get("commandProtocol") == "nvme":
                        nvmeof_props = (
                            prop.get("nvmeProperties", {}).get("nvmeofProperties", {}) or {}
                        )
                        # Could be ibProperties, roceV2Properties etc.
                        for props_key in ["ibProperties", "roceV2Properties"]:
                            addr_data = (
                                nvmeof_props.get(props_key, {}).get("ipAddressData", {}) or {}
                            )
                            ipv4_data = addr_data.get("ipv4Data", {}) or {}
                            ip = ipv4_data.get("ipv4Address")
                            if ip and ip != "0.0.0.0":
                                portals.append(
                                    {
                                        "address": ip,
                                        "port": nvmeof_props.get(props_key, {}).get(
                                            "listeningPort", 4420
                                        ),
                                    }
                                )
                                break  # Found an IP for this interface

            if portals:
                settings["portals"] = portals

        return settings

    def get_fc_target_settings(self) -> dict[str, Any]:
        """Get Fibre Channel target interfaces.

        Returns:
            A list of dictionary containing target WWPNs and other details.
        """
        return self._get("/fibre-channel/interface")
