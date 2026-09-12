import pytest
from unittest.mock import MagicMock
from santricity_client.automation.volumecopy import VolumeCopyAutomation

@pytest.fixture
def mock_client():
    client = MagicMock()
    return client

def test_get_system_load(mock_client):
    mock_client.request.return_value = {
        "cpuAvgUtilization": 0.09,
        "combinedIOps": 1111.6,
        "combinedThroughput": 6.09,
        "maxPossibleIopsUnderCurrentLoad": 62040.0
    }
    automation = VolumeCopyAutomation(mock_client)
    metrics = automation.get_system_load()
    
    assert metrics["controller_cpu_percent"] == 9.0
    assert metrics["overall_iops"] == 1111.6
    assert metrics["overall_throughput_mbps"] == 6.09
    assert metrics["max_possible_iops"] == 62040.0

def test_cleanup_completed_copies(mock_client):
    mock_client.volumes.list_copies.return_value = [
        {"volcopyRef": "ref1", "status": "complete"},
        {"volcopyRef": "ref2", "status": "inProgress"},
        {"volcopyRef": "ref3", "status": "failed"},
    ]
    automation = VolumeCopyAutomation(mock_client)
    automation.cleanup_completed_copies()
    
    assert mock_client.volumes.delete_copy.call_count == 2
    mock_client.volumes.delete_copy.assert_any_call("ref1", retain_repositories=False)
    mock_client.volumes.delete_copy.assert_any_call("ref3", retain_repositories=False)

def test_evaluate_and_adjust_copies(mock_client):
    # Mock single active job and mock stats for "low utilization" priority boost
    mock_client.volumes.list_copies.return_value = [
        {"volcopyRef": "active1", "status": "inProgress", "copyPriority": "priority1", "sourceVolume": "vol1"}
    ]
    mock_client.request.return_value = {"cpuAvgUtilization": 0.50} # 50% CPU
    mock_client.volumes.get.return_value = {"capacity": "1073741824"} # 1 GB
    
    automation = VolumeCopyAutomation(mock_client)
    
    # Needs a mock replacement because evaluate_and_adjust_copies calls cleanup_completed_copies which calls list_copies again
    # We will just patch cleanup_completed_copies for this isolated test
    automation.cleanup_completed_copies = MagicMock()
    
    automation.evaluate_and_adjust_copies(max_cpu_threshold=70.0, max_size_bytes=64 * 1024**3)
    
    mock_client.volumes.update_copy.assert_called_once_with("active1", priority="priority3")

def test_evaluate_and_adjust_copies_high_load(mock_client):
    # Mock high utilization which restricts to priority2
    mock_client.volumes.list_copies.return_value = [
        {"volcopyRef": "active1", "status": "inProgress", "copyPriority": "priority3", "sourceVolume": "vol1"}
    ]
    mock_client.request.return_value = {"cpuAvgUtilization": 0.85} # 85% CPU > 70% threshold
    mock_client.volumes.get.return_value = {"capacity": "1073741824"}
    
    automation = VolumeCopyAutomation(mock_client)
    automation.cleanup_completed_copies = MagicMock()
    
    automation.evaluate_and_adjust_copies(max_cpu_threshold=70.0)
    
    # Should downgrade to priority2 because CPU threshold exceeded
    mock_client.volumes.update_copy.assert_called_once_with("active1", priority="priority2")
