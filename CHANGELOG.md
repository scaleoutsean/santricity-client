# Changelog

All notable changes to this project will be documented here.

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
