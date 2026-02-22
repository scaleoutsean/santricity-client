# santricity-client

[![CI](https://github.com/scaleoutsean/santricity-client/actions/workflows/ci.yml/badge.svg)](https://github.com/scaleoutsean/santricity-client/actions/workflows/ci.yml)

A lightweight Python client library and CLI for managing NetApp E-Series SANtricity systems over the REST API.

The goal is to provide a consistent abstraction for the most frequently used storage-management actions while keeping the codebase easy to extend as new requirements emerge:

- Storage pools (list only)
- Volume
- Host(s)
- Volume mappings

Additional features can be added as required.

This makes `santricity-client` suitable for most Day 1+ needs and convenient use in automation pipelines and integrations.

## Features

- Configurable authentication strategies: Basic, JWT bearer token, and a pluggable SAML2 placeholder for future use.
- `requests`-based HTTP layer with retry-friendly hooks and centralized error translation.
- Modular resource surface area (pools, volumes, interfaces, hosts, snapshots, mappings, clones) to keep the client maintainable.
- Capability matrix with feature flags to smooth over SANtricity firmware differences and provide graceful fallbacks.
- Optional Typer-powered CLI for day-to-day listing and provisioning tasks.
- Type-hinted models and utility helpers intended to keep responses predictable across applications.
- Pytest test suite with `requests-mock` fixtures for offline validation.

## Quick Start

```bash
pip install -e .[dev]
```

```python
from santricity_client import SANtricityClient
from santricity_client.auth.basic import BasicAuth

client = SANtricityClient(
    base_url="https://array01.example.com/devmgr/v2",
    auth_strategy=BasicAuth(username="admin", password="secret"),
    release_version="11.94",
    system_id="600A098000F63714000000005E79C17C",  # storage-system WWN (see below)
)

for pool in client.pools.list():
    label = pool.get("label", "<unnamed>")
    total_size = pool.get("totalRaidedSpace")
    used_space = pool.get("usedSpace")
    free_space = pool.get("freeSpace")
    print(label, total_size, used_space, free_space)
```

## Project Layout

- `src/santricity_client`: library code split into auth strategies, HTTP helpers, and resource modules.
- `tests`: pytest-based regression tests with `requests-mock`.

## Development

1. Create a virtual environment (`uv`, `venv`, or your preferred tool).
2. Install dependencies and dev tooling.
   ```bash
   pip install -e .[dev]
   ```
3. Run formatting and tests.
   ```bash
   ruff check .
   pytest
   ```

## Command-Line Interface

Install the optional CLI extra (automatically included with `[dev]`):

```bash
pip install -e .[cli]
```

### Storage-System Scoping

Every SANtricity v2 request must include the storage-system identifier (WWN) in the path: `/devmgr/v2/storage-systems/<wwn>/...`. Pass the WWN via the `system_id` argument (Python) or `--system-id` flag (CLI). If you omit it, the client auto-discovers the first entry from `/storage-systems`, but providing the explicit WWN avoids accidentally targeting the implicit "system 1" wildcard.

Fetch the WWN once per session:

```bash
santricity system version \
    --base-url https://array01.example.com/devmgr/v2 \
    --username admin \
    --password secret
```

Or programmatically:

```python
system_info = client.system.release_summary()
print(system_info["version"], system_info.get("bundleDisplay"))
print(system_info.get("errors"))
```

### TLS Verification Options

- TLS verification is enabled by default and uses the host CA store.
- Pass `--no-verify` (or `SANTRICITY_VERIFY_SSL=0`) when you must talk to arrays that only expose self-signed certificates. The client now suppresses `urllib3` warning spam for that mode so output stays readable.
- Provide `--cert /path/to/ca-bundle.pem` (or set `SANTRICITY_CA_CERT`) to trust a custom CA bundle without disabling verification outright. The CLI validates the file exists and refuses to mix `--cert` with `--no-verify`.
- Any connection failure surfaces the root error raised by `requests`/`urllib3` (for example `CERTIFICATE_VERIFY_FAILED`) inside the CLI, making it easier to diagnose TLS issues quickly.

Use `--no-verify` to skip TLS verification for self-signed certificates.

Environment variables supported by the CLI:

- `SANTRICITY_VERIFY_SSL`: when set, the CLI will use this value as the default for `--verify/--no-verify`.
    - Common falsey values are accepted to disable verification: `0`, `false`, `no`, `off` (case-insensitive).
    - Any other value (or an absent variable) enables verification by default.
- `SANTRICITY_CA_CERT`: path to a PEM file to use as a custom CA bundle (equivalent to `--cert /path/to/ca-bundle.pem`).

Examples:

```sh
export SANTRICITY_VERIFY_SSL=0
export SANTRICITY_CA_CERT=/path/to/ca-bundle.pem
```

Notes:

- The CLI refuses to combine a custom CA bundle with disabled verification (for example `SANTRICITY_CA_CERT` with `SANTRICITY_VERIFY_SSL=0`).
- When verification is disabled the client suppresses `urllib3`'s `InsecureRequestWarning` for cleaner CLI output.

### CLI Examples

In additoin to command-line flags, the CLI honors these environment variables for convenience:

```sh
$ export SANTRICITY_BASE_URL=https://controller_b:8443/devmgr/v2
$ export SANTRICITY_USERNAME=admin
$ export SANTRICITY_PASSWORD=secret
```

List pools:

```bash
santricity pools list \
    --base-url https://array/devmgr/v2 \
    --system-id 600A098000F63714000000005E79C17C \
    --username admin \
    --password secret \
    --no-verify # skip TLS verification if needed
```

Create a volume:

```bash
santricity volumes create \
    --base-url https://array/devmgr/v2 \
    --system-id 600A098000F63714000000005E79C17C \
    --username admin \
    --password secret \
    --pool-id 0400 \
    --name demo \
    --size 10 \
    --size-unit gb \
    --require-unique-name
```

The CLI validates uniqueness by default. Supply `--allow-duplicate-name` only when you intentionally need two volumes with the same label.

### Create host 

This client currently suppors one initiator per host, which seems to be the norm anyway.

iSCSI hosts can be created with IQN and optionally client-side CHAP credentials:

```python
client.hosts.add_initiator(
    host_ref="...", 
    name="iqn.2010-01.com.example:...", 
    type="iscsi", 
    chap_secret="secret123"
)
```

NVMe/RoCE hosts can be defined (one port per host) like so:

```python
client.hosts.add_initiator(
    host_ref="...",
    name="nqn.2014-08.org.nvmexpress:uuid:...",
    type="nvmeof",
    label="my-nvme-initiator"
)
```

Once hosts are added, hosts groups can be formed without protocol-specific information.

### Power-user extras

You can include arbitrary key/value pairs in the API payload using the `--extras` flag. Provide comma-separated `k=v` pairs; values are coerced to booleans, numbers, or `None` when appropriate. Example:

```bash
santricity volumes create \
    --base-url https://array/devmgr/v2 \
    --system-id 600A098000F63714000000005E79C17C \
    --username admin \
    --password secret \
    --pool-id 0400 \
    --name demo \
    --size 10 \
    --size-unit gb \
    --extras enableCache=True,someVar=1
```

Notes:
- Extras are merged into the generated payload and take precedence over named CLI options (power-user convenience).
- For complex or nested payloads prefer `--payload` (path to a JSON file) or using `--json` with programmatic clients.
 - If you supply size-related values via `--extras`, provide sizes in bytes (the CLI's `--size`/`--size-unit` helpers are not applied to extras).


Audit duplicate names at any time:

```bash
santricity volumes check-names \
    --base-url https://array/devmgr/v2 \
    --system-id 600A098000F63714000000005E79C17C \
    --username admin \
    --password secret
```

The command exits with a non-zero status if duplicates are found, printing the conflicting names and their `volumeRef` identifiers for safe remediation.

List mappings:

```bash
santricity mappings list \
    --base-url https://array/devmgr/v2 \
    --system-id 600A098000F63714000000005E79C17C \
    --username admin \
    --password secret
```

Use `--resolve` to resolve volume and storage pool names and show them instead of the long IDs.

Map a volume to a specific host (even if it belongs to a host group):

```bash
santricity mappings create \
    --base-url https://array/devmgr/v2 \
    --system-id 600A098000F63714000000005E79C17C \
    --username admin \
    --password secret \
    --volume-ref 12345 \
    --host app-01
```

The command accepts exactly one of `--host`, `--host-ref`, `--host-group`, or `--cluster-ref`. Mapping directly to a host that resides inside a host group is valid—the host simply receives an individual LUN assignment—while mapping to the host group (`--host-group`/`--cluster-ref`) shares the volume across every host in that cluster.

Review host membership to decide which scope to target:

```bash
santricity hosts membership \
    --base-url https://array/devmgr/v2 \
    --system-id 600A098000F63714000000005E79C17C \
    --username admin \
    --password secret
```

The helper lists each host alongside the `hostGroup` (if any) so operators can see whether a host already participates in a cluster before mapping new LUNs.

Inspect the controller software version reported by both the firmware bundle metadata and the legacy `symbolapi` endpoint:

```bash
santricity system version \
    --base-url https://array/devmgr/v2 \
    --username admin \
    --password secret
```

The command returns a JSON summary that includes the bundle display string (`11.90R2` in the sample output), management firmware build, and symbol API identifiers so you can feed the detected release back into automation without guessing.

## Releasing

Note: this package *may* be published to PyPI, but that is unlikely because I think there isn't enough interest in this library to justify the burden of maintaining a PyPI package.

- Update `CHANGELOG.md` and bump the version in `pyproject.toml`.
- Build the package with `python -m build`.
- Publish to PyPI via `twine upload dist/*`.
