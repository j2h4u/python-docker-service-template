from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from venv import EnvBuilder


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="template-service-packaging-") as tmp:
        workdir = Path(tmp)
        dist_dir = workdir / "dist"
        venv_dir = workdir / "venv"
        constraints_file = workdir / "runtime-constraints.txt"

        _run(["uv", "build", "--wheel", "--out-dir", str(dist_dir), "--no-build-logs", str(repo_root)])

        wheel_files = sorted(dist_dir.glob("*.whl"))
        if len(wheel_files) != 1:
            raise RuntimeError(f"expected exactly one wheel, found {len(wheel_files)} in {dist_dir}")

        EnvBuilder(with_pip=False, clear=True).create(venv_dir)
        executable = venv_dir / "bin" / "template-service"
        venv_python = venv_dir / "bin" / "python"
        if not venv_python.is_file():
            raise RuntimeError(f"venv python not found: {venv_python}")

        _run(
            [
                "uv",
                "export",
                "--locked",
                "--no-dev",
                "--no-emit-project",
                "--no-emit-workspace",
                "--no-emit-local",
                "--no-header",
                "--no-annotate",
                "--no-hashes",
                "--no-editable",
                "--output-file",
                str(constraints_file),
            ],
            cwd=repo_root,
        )
        install_env = {**os.environ, "UV_LINK_MODE": "copy"}
        _run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(venv_python),
                "--constraint",
                str(constraints_file),
                str(wheel_files[0]),
            ],
            env=install_env,
        )
        smoke_dir = workdir / "smoke"
        smoke_dir.mkdir()
        smoke_env = {**os.environ, "PYTHONSAFEPATH": "1"}
        for variable in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
            smoke_env.pop(variable, None)
        _run([str(executable), "--help"], cwd=smoke_dir, env=smoke_env)
        _run([str(executable), "health"], cwd=smoke_dir, env=smoke_env)

    print("packaging smoke passed: wheel built, installed, CLI help and health ran")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
