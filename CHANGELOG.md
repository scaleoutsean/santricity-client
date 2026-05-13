# Changelog

All notable changes to this project will be documented here.

## 0.2.9

- Add `initial_repo_group_size_pct` support to `auto_create_snapshot` for snapshot group capacity control.

## 0.2.8

- Consistency Group snapshots and read-only Linked Clones (client library and CLI)

## 0.2.7 

- Expose automation snapshot as public SDK method for auto_create_snapshot

## 0.2.6

- Populate non-missing, but incorrectly returned as null, value of controllerRef in interfaces report

## 0.2.5

- Populate empty controllerRef with known for interfaces report

## 0.2.4

- Change text to bool output for Ethernet in interfaces report

## 0.2.2 and 0.2.3

- Rename "Ready" column to "NVMe Ready" in interfaces report
- Fix one of the tests

## 0.2.1

- Add interfaces report and more snapshot-related commands

## 0.2.0

- Add get_system_hostside_interfaces for interface
- Fix: get NVMeoF initiator now just pass-through

## 0.1.9

- Fix: remove failback path for NVMeoF initiator

## 0.1.8

- Fix: correct querying of NVMe and ISCSI settings

## 0.1.7

- CLI: add repo group and snapshot group create commands
- Fix: make `system_id` public

## 0.1.6

- CLI: add snapshot create commands
- Add `-h` as alias for `--help`

## 0.1.5

- Snapshots: list for most snapshot-related commands, and create/delete snapshot for individual volumes

## 0.1.4

- Volume helper: client-side filter to find-volume-by-name helper, takes optional pool name 

## 0.1.3

- Add create, update, delete support for hosts and host groups (iSCSI, NVMe/RoCE; with FC accepted (but not tested) as well)
- Target/Portal resolution (iSCSI, NVMe/RoCE; with FC accepted (but not tested) as well)
- Pool helper: find pool ID by pool name
- Host helper: find host by name or initiator (IQN or NQN; with FC supported (but not tested) as well)
- Mapping logic improvement - if a target (volume) is mapped to a host that's member of a cluster ("host group"), mapping will present volume to the host's group 

## 0.1.2

- Volume resize 

## 0.1.1

- NVMe-oF support for (GET) `hosts` object

## 0.1.0
- Initial release aimed at common daily tasks and manipulating their objects (volume, host, mappings), includes a client library and CLI
