# Snapshots 

## Limits

According to [TR-4747](https://www.netapp.com/media/17167-tr4747.pdf):

|  Maximum              | System |
| :---------------------| :------------------: |
| Snapshots/system      | 1,024 (EF300), 2,048 |
| Snapshot groups/system| 512 (EF300), 1,024   |
| Snapshot groups/volume| 4     |
| Snapshots/group       | 32    |
| Volumes/CG            | 64    |
| Consistency Group/system  | 32|
| Linked Clones/system  | 1,024 |
| Linked Clones/snapshot| 4     |
| Concurrent rollbacks/system | 8 |
| Repos volumes / repo group  | 16 |

## Usage

### Orphaned repository volumes

Orphaned repository volumes may be left over in case of disorderly deletion of Base Volume (which SANtricity does not prevent). The TR says such volumes can be reused. They can, but maybe they shouldn't be: SANtricity Client doesn't try to be smart about this. It is recommended to perform orderly deletion of resources and not speculate whether some orphaned volume would or wouldn't be suitable for reuse because that's often hard to tell.

```sh
santricity snapshots list-repo-volumes
santricity snapshots create-repo-group --volume vol1 --use-free-repository-volumes --percent-capacity 15
```

### Auto snapshot policy

`create-snapshot --auto` can be configured to enforce minimum repository headroom before taking a snapshot.

- `--min-free-percent`: minimum free capacity required in the selected snapshot group's repository
- `--auto-grow-if-needed` (default): when no group meets minimum free capacity, the client can grow one eligible repository group
- `--growth-step-percent`: requested expansion size as a percent of base volume
- `--max-repo-volumes-per-group`: safety cap for concat members (default 16)
- `--max-repo-group-capacity-percent`: safety cap to avoid growing very large repositories

Example:

```sh
santricity snapshots create-snapshot \
  --auto \
  --volume vol1 \
  --min-free-percent 10 \
  --growth-step-percent 10
```

Selection and growth are evaluated per base volume. This means consistency-group style workflows can reuse the same checks by applying them to each member volume's snapshot group. Depending on circumstances, one member's repo group may be extended, while the rest may remain unchanged.
