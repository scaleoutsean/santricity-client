import pytest
from unittest.mock import MagicMock
from santricity_client.automation.snapshots import SnapshotsAutomation

def test_create_cg_snapshot_success():
    client = MagicMock()
    automation = SnapshotsAutomation(client)
    
    # Mock members
    client.consistency_groups.list_member_volumes.return_value = [{"id": "vol1"}]
    client.consistency_groups.create_snapshot.return_value = [{"id": "snap1"}]
    
    res = automation.create_cg_snapshot("cg1")
    assert res == [{"id": "snap1"}]
    client.consistency_groups.list_member_volumes.assert_called_once_with("cg1")
    client.consistency_groups.create_snapshot.assert_called_once_with("cg1")

def test_create_cg_snapshot_fails_if_empty():
    client = MagicMock()
    automation = SnapshotsAutomation(client)
    
    # Mock empty members
    client.consistency_groups.list_member_volumes.return_value = []
    
    with pytest.raises(RuntimeError, match="it has no member volumes"):
        automation.create_cg_snapshot("cg1")
        
    client.consistency_groups.list_member_volumes.assert_called_once_with("cg1")
    client.consistency_groups.create_snapshot.assert_not_called()
