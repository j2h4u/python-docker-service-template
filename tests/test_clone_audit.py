import json
import os
import sys
import time
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest
from scripts import clone_audit


def _report(output: Path) -> dict[str, object]:
    return cast("dict[str, object]", json.loads((output / "audit.json").read_text()))


def test_offline_default_and_fresh_reports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = Mock(return_value="")
    monkeypatch.setattr(clone_audit, "_run", run)
    assert clone_audit.main(["--output", str(tmp_path)]) == 0
    first = _report(tmp_path)
    assert first["state"] == "complete"
    assert first["scope"] == ["src", "scripts"]
    assert run.call_count == 1
    assert "--semantic" not in run.call_args.args[0]
    run.side_effect = RuntimeError("native failure")
    assert clone_audit.main(["--output", str(tmp_path), "--include-tests"]) == 1
    second = _report(tmp_path)
    assert second["state"] == "failed"
    assert second["run"] != first["run"]
    assert second["scope"] == ["src", "scripts", "tests"]


@pytest.mark.parametrize(
    "extra",
    [[], ["--endpoint", "https://example.invalid/v1"], ["--endpoint", "http://example.invalid/v1", "--model", "fixed"]],
)
def test_semantic_requires_explicit_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    extra: list[str],
) -> None:
    monkeypatch.setenv("JSCPD_SEMANTIC_API_KEY", "fixture-secret")
    run = Mock()
    monkeypatch.setattr(clone_audit, "_run", run)
    assert clone_audit.main(["--output", str(tmp_path), "--semantic", *extra]) == 1
    run.assert_not_called()
    assert _report(tmp_path)["state"] == "failed"


def test_semantic_failure_is_incomplete_and_redacts_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JSCPD_SEMANTIC_API_KEY", "fixture-secret")
    monkeypatch.setattr(clone_audit, "inventory", Mock(return_value={"src/main.py": "pass\n"}))
    monkeypatch.setattr(clone_audit, "_run", Mock(side_effect=["", RuntimeError("fixture-secret refused")]))
    assert (
        clone_audit.main(
            [
                "--output",
                str(tmp_path),
                "--semantic",
                "--endpoint",
                "http://127.0.0.1:9/v1",
                "--model",
                "fixed",
            ]
        )
        == 1
    )
    assert _report(tmp_path)["state"] == "incomplete"
    assert "fixture-secret" not in (tmp_path / "audit.json").read_text()


@pytest.mark.parametrize("endpoint", ["https://user:password@example.invalid/v1", "https://x/v1?key=secret"])
def test_endpoint_rejects_credentials(endpoint: str) -> None:
    with pytest.raises(ValueError, match="credentials"):
        clone_audit._endpoint(endpoint)


def test_deadline_kills_child_process() -> None:
    with pytest.raises(TimeoutError, match="deadline"):
        clone_audit._run(
            [sys.executable, "-c", "import time; time.sleep(30)"], Path.cwd(), time.monotonic() + 0.05, dict(os.environ)
        )


def test_native_error_is_redacted() -> None:
    with pytest.raises(RuntimeError, match="redacted") as error:
        clone_audit._run(
            [sys.executable, "-c", "print('fixture-secret'); raise SystemExit(1)"],
            Path.cwd(),
            time.monotonic() + 2,
            dict(os.environ, JSCPD_SEMANTIC_API_KEY="fixture-secret"),
        )
    assert "fixture-secret" not in str(error.value)


def test_timeout_budget_is_shared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clone_audit, "_run", Mock(side_effect=TimeoutError("total deadline")))
    assert clone_audit.main(["--output", str(tmp_path), "--timeout", "0.01"]) == 1
    assert _report(tmp_path)["state"] == "failed"


def test_missing_key_prevents_semantic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JSCPD_SEMANTIC_API_KEY", raising=False)
    run = Mock()
    monkeypatch.setattr(clone_audit, "_run", run)
    assert (
        clone_audit.main(["--semantic", "--endpoint", "https://x/v1", "--model", "fixed", "--output", str(tmp_path)])
        == 1
    )
    run.assert_not_called()


@pytest.mark.parametrize("valid", [False, True])
def test_semantic_validates_native_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    valid: bool,
) -> None:
    monkeypatch.setattr(clone_audit, "inventory", Mock(return_value={"src/main.py": "pass\n"}))

    def native(command: list[str], _root: Path, _deadline: float, env: dict[str, str]) -> str:
        assert env["JSCPD_CACHE_DIR"] == str(tmp_path / "cache")
        assert "--semantic-download" not in command
        assert command[-1] == "src/main.py"
        report: dict[str, object] = {"duplicates": []}
        if valid:
            report["statistics"] = {"total": {"clones": 0, "sources": 1}}
        (tmp_path / "semantic" / "jscpd-report.json").write_text(json.dumps(report))
        return ""

    monkeypatch.setattr(clone_audit, "_run", native)
    args = clone_audit._arguments(
        [
            "--semantic",
            "--endpoint",
            "http://127.0.0.1/v1",
            "--model",
            "fixed",
            "--output",
            str(tmp_path),
        ]
    )
    if valid:
        clone_audit._semantic(args, tmp_path, tmp_path, time.monotonic() + 2)
    else:
        with pytest.raises(KeyError):
            clone_audit._semantic(args, tmp_path, tmp_path, time.monotonic() + 2)
