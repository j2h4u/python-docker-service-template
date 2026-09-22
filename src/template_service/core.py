from importlib.metadata import version


def health_status() -> str:
    return "ok"


def package_version() -> str:  # pragma: no mutate block
    return version("python-docker-service-template")
