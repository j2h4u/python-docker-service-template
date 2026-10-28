import json
import re
from pathlib import Path
from textwrap import dedent

import pytest
from coverage import Coverage
from scripts.crap_gate import _function_metrics_from_report, _load_coverage_report
from scripts.crap_gate import main as crap_gate_main


def _real_coverage(tmp_path: Path, source: str) -> tuple[Path, Path]:
    source_root = tmp_path / "src"
    source_root.mkdir()
    module = source_root / "worker.py"
    module.write_text(dedent(source), encoding="utf-8")
    measurement = Coverage(data_file=None, config_file=False, include=[str(module)])
    measurement.start()
    try:
        exec(compile(module.read_text(encoding="utf-8"), str(module), "exec"), {})
    finally:
        measurement.stop()
    report = tmp_path / "coverage.json"
    measurement.json_report(outfile=str(report))
    return source_root, report


def test_local_method_exceeding_crap_threshold_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source_root, report = _real_coverage(
        tmp_path,
        """
        def factory():
            class Worker:
                def run(self, value):
                    if value == 0:
                        return 0
                    if value == 1:
                        return 1
                    if value == 2:
                        return 2
                    if value == 3:
                        return 3
                    if value == 4:
                        return 4
                    return value
            return Worker
        factory()
        """,
    )

    assert crap_gate_main(["--coverage", str(report), "--src", str(source_root)]) == 1
    assert "factory.Worker.run" in capsys.readouterr().out
    metrics = _function_metrics_from_report(_load_coverage_report(report), source_root)
    method = next(metric for metric in metrics if metric.key.endswith("::factory.Worker.run"))
    assert method.complexity == 6
    assert method.coverage_fraction == 0
    assert method.crap == 42


_SCOPED_SOURCE = """
class Worker:
    def run(self):
        return 1

def factory():
    class Worker:
        async def run(self):
            def finish():
                return 2
            return finish()
        class Nested:
            def run(self):
                return 3
    def closure():
        class Worker:
            def run(self):
                class Deep:
                    def run(self):
                        return 4
                return Deep
        return Worker
    return Worker, closure

def other():
    class Worker:
        def run(self):
            return 5
    return Worker

factory()
other()
"""

_SCOPED_NAMES = {
    "Worker.run",
    "factory",
    "factory.Worker.run",
    "factory.Worker.run.finish",
    "factory.Worker.Nested.run",
    "factory.closure",
    "factory.closure.Worker.run",
    "factory.closure.Worker.run.Deep.run",
    "other",
    "other.Worker.run",
}


def test_local_methods_and_closures_match_real_coverage(tmp_path: Path) -> None:
    source_root, report = _real_coverage(tmp_path, _SCOPED_SOURCE)
    coverage_report = _load_coverage_report(report)
    functions = next(iter(coverage_report["files"].values()))["functions"]

    assert set(functions) - {""} == _SCOPED_NAMES
    metrics = _function_metrics_from_report(coverage_report, source_root)
    assert {metric.key.removeprefix("worker.py::") for metric in metrics} == _SCOPED_NAMES
    assert all(metric.complexity == 1 for metric in metrics)
    assert crap_gate_main(["--coverage", str(report), "--src", str(source_root)]) == 0


@pytest.mark.parametrize("missing", sorted(_SCOPED_NAMES))
def test_missing_scoped_function_coverage_fails(tmp_path: Path, missing: str) -> None:
    source_root, report = _real_coverage(tmp_path, _SCOPED_SOURCE)
    coverage_report = _load_coverage_report(report)
    functions = next(iter(coverage_report["files"].values()))["functions"]
    del functions[missing]
    report.write_text(json.dumps(coverage_report), encoding="utf-8")

    with pytest.raises(ValueError, match=re.escape(missing)):
        _function_metrics_from_report(coverage_report, source_root)
    assert crap_gate_main(["--coverage", str(report), "--src", str(source_root)]) == 1


def test_unmatched_function_coverage_fails(tmp_path: Path) -> None:
    source_root, report = _real_coverage(tmp_path, _SCOPED_SOURCE)
    coverage_report = _load_coverage_report(report)
    functions = next(iter(coverage_report["files"].values()))["functions"]
    functions["stale.run"] = functions["factory.Worker.run"]
    report.write_text(json.dumps(coverage_report), encoding="utf-8")

    with pytest.raises(ValueError, match=r"stale\.run"):
        _function_metrics_from_report(coverage_report, source_root)
    assert crap_gate_main(["--coverage", str(report), "--src", str(source_root)]) == 1
