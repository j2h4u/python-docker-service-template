from __future__ import annotations

from pathlib import Path

import pytest
from scripts import check_packaging_smoke


def test_smoke_installs_wheel_with_runtime_constraints_exported_from_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], Path | None]] = []
    installed_constraints: list[str] = []

    def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
        del env
        calls.append((command, cwd))
        if command[:2] == ["uv", "build"]:
            output_dir = Path(command[command.index("--out-dir") + 1])
            output_dir.mkdir()
            (output_dir / "service.whl").touch()
        elif command[:2] == ["uv", "export"]:
            constraints = Path(command[command.index("--output-file") + 1])
            constraints.write_text("typer==0.27.2\n")
        elif command[:3] == ["uv", "pip", "install"]:
            constraints = Path(command[command.index("--constraint") + 1])
            installed_constraints.append(constraints.read_text())

    class FakeEnvBuilder:
        def __init__(self, *, with_pip: bool, clear: bool) -> None:
            assert with_pip is False
            assert clear is True

        def create(self, path: Path) -> None:
            python = path / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.touch()

    monkeypatch.setattr(check_packaging_smoke, "_run", run)
    monkeypatch.setattr(check_packaging_smoke, "EnvBuilder", FakeEnvBuilder)

    assert check_packaging_smoke.main() == 0

    export, export_cwd = next((call, cwd) for call, cwd in calls if call[:2] == ["uv", "export"])
    install, _ = next((call, cwd) for call, cwd in calls if call[:3] == ["uv", "pip", "install"])
    assert "--locked" in export
    assert "--no-dev" in export
    assert "--no-emit-project" in export
    assert "--no-emit-workspace" in export
    assert "--no-emit-local" in export
    assert export_cwd == Path(check_packaging_smoke.__file__).resolve().parents[1]
    assert installed_constraints == ["typer==0.27.2\n"]
    assert install[-1].endswith("service.whl")
