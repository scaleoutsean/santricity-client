# SANtricity Snapshots and Linked Clones

This document provides a walk-through for managing snapshots and read-only linked clones (Views, as SANtricity calls them) using the `santricity` CLI. It covers both single volumes and Consistency Groups (CGs). 

With a growing number of commands, this guide illustrates the correct order of operations, helping to distinguish between repository allocation, snapshot creation, and clone mapping.

---

## 1. Single Volume Snapshots and Clones

For single volumes, operations fall under the `santricity snapshots` command group.

### A. Creating a Snapshot

Taking a snapshot captures the point-in-time state of the volume.

```bash
# Create a snapshot for a volume. Repositories are automatically provisioned.
santricity snapshots create --volume-id vol-abc --name "snap-1"

# Verify it was created
santricity snapshots list --volume-id vol-abc
```

### B. Creating a Read-Only Linked Clone (View)

To mount or read from a snapshot without modifying it, you create a Read-Only Linked Clone (known as a "View" in the API).

```bash
# Create a clone from the snapshot
santricity snapshots create-clone --snapshot-id snap-1 --name "clone-snap-1"

# List your clones
santricity snapshots list-clones
```

### C. Restoring (Rolling Back) a Volume

*Destructive Operation!* If your primary volume suffers file system corruption or accidental deletion, you can roll the base volume back to the exact state of the snapshot.

```bash
# Revert the base volume to the snapshot's state
santricity snapshots restore <snapshot-id>
```

*(Note: Any data written to the base volume after the snapshot was taken will be lost. You may create another snapshot just before restoring, in case you think you may need that data. )*

**Monitoring Progress & Protections:**
- The CLI automatically checks to ensure no other snapshots are actively rolling back into the same base volume before proceeding.
- During the rollback, the base volume's `action` dynamically changes to `pitRollback`. Once finished, it returns to `none`. 
- *(Note: Snapshot rollbacks are tracked natively on the volume. In contrast, to check the progress of offline full volume copies, you would use `santricity volumes copy-status`).*
- [See the documentation for more](https://docs.netapp.com/us-en/e-series-santricity/sm-storage/start-snapshot-image-rollback-for-base-volume.html)

### D. Cleanup and Teardown

You cannot delete a snapshot if it has an active clone (View) dependent on it. Clean up from the top down:

```bash
# 1. Delete the clone
santricity snapshots delete-clone --clone-id clone-snap-1

# 2. Delete the snapshot
santricity snapshots delete --snapshot-id snap-1
```

---

## 2. Consistency Group (CG) Snapshots and Clones

For multi-volume crash consistency (like a database spanning multiple drives), operations fall under the `santricity consistency-groups` command group.

CGs abstract repository provisioning. You do not manually create repositories for CG members; the array allocates them invisibly when you add a member.

### A. Creating a Consistency Group & Adding Members

```bash
# 1. Create the empty Consistency Group
santricity consistency-groups create --name "db-cg"

# 2. Add volumes to the CG (this triggers background repository creation)
santricity consistency-groups add-member --cg-id cg-xyz --volume-id vol-db-data
santricity consistency-groups add-member --cg-id cg-xyz --volume-id vol-db-logs

# Verify members
santricity consistency-groups list-members --cg-id cg-xyz
```

### B. Creating a CG Snapshot

When you snapshot a CG, the array guarantees a crash-consistent point-in-time across all member volumes simultaneously.

```bash
# Take a snapshot of the entire Consistency Group
santricity consistency-groups create-snapshot --cg-id cg-xyz

# List the CG snapshots (returns pitSequenceNumbers or CG Snapshot IDs)
santricity consistency-groups list-snapshots --cg-id cg-xyz
```

### C. Creating CG Read-Only Linked Clones

If you need to mount the CG snapshot (e.g., for backup offload or testing), you expose it as a "View". Linked clones may be mapped to another host for access which also avoids confusing the original host(s) due to duplicate volume signatures.

```bash
# Create clones for the CG snapshot
santricity consistency-groups create-clone --cg-id cg-xyz --snapshot-id cg-snap-1

# List the clones to find their WWNs/IDs for host mapping
santricity consistency-groups list-clones --cg-id cg-xyz
```

### D. Reverting (Rolling Back) a Consistency Group

*Destructive Operation!* Revert all member volumes in the CG to the point-in-time snapshot simultaneously.

```bash
santricity consistency-groups rollback --cg-id cg-xyz --snapshot-id cg-snap-1
```

### E. Cleanup and Teardown

As with single volumes, you must unravel the dependencies from the top down.

```bash
# 1. Delete the CG Clone(s)
santricity consistency-groups delete-clone --cg-id cg-xyz --clone-id cg-clone-1

# 2. Delete the CG Snapshot
santricity consistency-groups delete-snapshot --cg-id cg-xyz --snapshot-id cg-snap-1

# 3. Remove members (This automatically deletes their invisible backing repositories)
santricity consistency-groups remove-member --cg-id cg-xyz --volume-id vol-db-data
santricity consistency-groups remove-member --cg-id cg-xyz --volume-id vol-db-logs

# 4. Delete the empty Consistency Group
santricity consistency-groups delete --cg-id cg-xyz
```

---

## Summary of use cases

*   **Single Volume:** Best for standalone, single-disk file servers, boot drives, or uncoupled applications. Use `santricity snapshots`.
*   **Consistency Group:** Best for databases (Data + Logs), clustered file systems, or multi-disk applications where writes must be frozen in standard order. Use `santricity consistency-groups`.
*   **Reverts:** Use only for critical recovery (i.e. filesystem corruption). Destroys current state of base volume(s).
*   **Linked Clones:** Use for mounting snapshots to hosts for analytics, backups, or testing. Read-only Linked Clones are sufficient for Linux backup applications.
