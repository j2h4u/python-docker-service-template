from typer.testing import CliRunner

from template_service.cli import app


def test_version_flag_reports_package_version() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"


def test_health_command_reports_ok() -> None:
    result = CliRunner().invoke(app, ["health"])

    assert result.exit_code == 0
    assert result.output.strip() == "ok"
