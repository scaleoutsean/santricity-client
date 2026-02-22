from typer.testing import CliRunner

from santricity_client.cli import app

runner = CliRunner()


def test_cli_respects_env_cert_and_verify_true(monkeypatch, tmp_path):
    cert = tmp_path / "ca.pem"
    cert.write_text("dummy", encoding="utf-8")
    captured: dict[str, object] = {}

    class DummyClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.pools = type("P", (), {"list": lambda self: []})()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("santricity_client.cli.SANtricityClient", DummyClient)

    result = runner.invoke(
        app,
        [
            "pools",
            "list",
            "--base-url",
            "https://array/devmgr/v2",
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            "600A098000F63714",
        ],
        env={"SANTRICITY_CA_CERT": str(cert), "SANTRICITY_VERIFY_SSL": "1"},
    )

    assert result.exit_code == 0
    assert captured["verify_ssl"] == str(cert)


def test_cli_env_cert_with_no_verify_rejected(tmp_path):
    cert = tmp_path / "ca.pem"
    cert.write_text("dummy", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "pools",
            "list",
            "--base-url",
            "https://array/devmgr/v2",
            "--username",
            "admin",
            "--password",
            "secret",
            "--system-id",
            "600A098000F63714",
        ],
        env={"SANTRICITY_CA_CERT": str(cert), "SANTRICITY_VERIFY_SSL": "0"},
    )

    assert result.exit_code != 0
    assert "Cannot combine --cert with --no-verify" in result.stderr
