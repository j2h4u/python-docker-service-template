import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("failed_command", ["", "up", "exec"])
def test_runtime_smoke_owns_project_and_cleanup(tmp_path: Path, failed_command: str) -> None:
    docker = tmp_path / "docker"
    docker.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$DOCKER_LOG"
if [[ -n "$FAILED_COMMAND" && "${4:-}" == "$FAILED_COMMAND" ]]; then
    exit 23
fi
""",
        encoding="utf-8",
    )
    docker.chmod(0o755)
    log = tmp_path / "docker.log"
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}", DOCKER_LOG=str(log), FAILED_COMMAND=failed_command)
    root = Path(__file__).resolve().parents[1]

    for _ in range(2):
        result = subprocess.run(
            ["just", "runtime-smoke"], cwd=root, env=env, capture_output=True, text=True, check=False, timeout=15
        )
        assert result.returncode == (23 if failed_command else 0), result.stderr

    commands = [line.split() for line in log.read_text(encoding="utf-8").splitlines()]
    validations = [
        command for command in commands if command[:2] == ["compose", "config"] or command[:2] == ["build", "--check"]
    ]
    assert len(validations) == 4
    projects = {command[2] for command in commands if command[:2] == ["compose", "-p"]}
    assert len(projects) == 2
    assert all(project.startswith("python-docker-service-template-smoke-") for project in projects)
    for project in projects:
        owned_commands = [
            command[3:] for command in commands if command[:2] == ["compose", "-p"] and command[2] == project
        ]
        actions = [command[0] for command in owned_commands]
        assert "up" in actions and "down" in actions
        assert ("exec" in actions) == (failed_command != "up")
        cleanup = next(command for command in owned_commands if command[0] == "down")
        assert {"-v", "--remove-orphans", "--rmi", "local"} <= set(cleanup)
        assert all(command[0] in {"up", "exec", "ps", "logs", "down"} for command in owned_commands)
