import pytest
from unittest import mock
from typer.testing import CliRunner
from santricity_client.cli import app
from requests_mock import Mocker

runner = CliRunner()

def test_cgs_list(requests_mock: Mocker):
    requests_mock.get(
        "https://array/devmgr/v2/storage-systems/test_sys/consistency-groups",
        json=[{"name": "cg1", "id": "123"}],
    )
    result = runner.invoke(app, ["consistency-groups", "list", "--system-id", "test_sys", "--base-url", "https://array/devmgr/v2", "-u", "a", "-p", "b", "--no-verify"])
    assert result.exit_code == 0
    assert "cg1" in result.stdout

def test_cgs_create(requests_mock: Mocker):
    requests_mock.post(
        "https://array/devmgr/v2/storage-systems/test_sys/consistency-groups",
        json={"name": "new_cg", "id": "123"},
    )
    result = runner.invoke(app, ["consistency-groups", "create", "--name", "new_cg", "--system-id", "test_sys", "--base-url", "https://array/devmgr/v2", "-u", "a", "-p", "b", "--no-verify"])
    assert result.exit_code == 0
    assert "new_cg" in result.stdout

