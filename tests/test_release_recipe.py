import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=QA Fixture", "-c", "user.email=qa@example.invalid", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    shutil.copyfile(root / "Justfile", tmp_path / "Justfile")
    shutil.copytree(root / "scripts", tmp_path / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    _git(tmp_path, "init", "--quiet", "--initial-branch=main")
    _git(tmp_path, "commit", "--quiet", "--allow-empty", "-m", "chore: initial")
    _git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(tmp_path, "commit", "--quiet", "--allow-empty", "-m", "fix: repair fixture")
    return tmp_path


def _release_check(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["just", "release-check", *arguments],
        cwd=repository,
        env={**os.environ, "UV_OFFLINE": "1"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_release_check_preserves_quoted_values_as_data(repository: Path) -> None:
    _git(repository, "commit", "--quiet", "--allow-empty", "-m", "test: second fixture commit")
    body = repository / "notes ' $(touch injected).md"
    body.write_text("BEGIN_COMMIT_OVERRIDE\nfix: repair fixture\nEND_COMMIT_OVERRIDE\n", encoding="utf-8")

    result = _release_check(repository, "fix: don't run $(touch injected)", body.name)

    assert result.returncode == 0, result.stderr
    assert "Override block parses into 1" in result.stdout
    assert not (repository / "injected").exists()


def test_release_check_defaults_to_the_first_commit_title(repository: Path) -> None:
    result = _release_check(repository)

    assert result.returncode == 0, result.stderr
    assert "PR title is releasable" in result.stdout


def test_release_check_rejects_an_invalid_title(repository: Path) -> None:
    result = _release_check(repository, "not a release title")

    assert result.returncode != 0
    assert "PR title must look like" in result.stderr


def test_release_check_requires_multi_commit_override(repository: Path) -> None:
    _git(repository, "commit", "--quiet", "--allow-empty", "-m", "test: second fixture commit")

    result = _release_check(repository, "fix: repair fixture")

    assert result.returncode != 0
    assert "BEGIN_COMMIT_OVERRIDE" in result.stderr
