from importlib.metadata import version

from template_service.core import health_status, package_version


def test_health_status_reports_ok() -> None:
    assert health_status() == "ok"


def test_package_version_reports_installed_distribution_version() -> None:
    assert package_version() == version("python-docker-service-template")
