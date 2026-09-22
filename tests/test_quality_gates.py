import json
from pathlib import Path

import pytest
from scripts.check_mutation_gate import check_mutation_gate
from scripts.check_supply_chain_pins import _check_action_refs, _check_container_refs
from scripts.crap_gate import main as crap_gate_main


def test_supply_chain_pin_check_rejects_dash_uses_steps(tmp_path: Path) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        """
name: CI
jobs:
  test:
    steps:
      - uses: example/action@main
""",
        encoding="utf-8",
    )

    errors = _check_action_refs(tmp_path)

    assert any("example/action@main" in error for error in errors)


def test_supply_chain_pin_check_rejects_quoted_uses_refs(tmp_path: Path) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        """
name: CI
jobs:
  test:
    steps:
      - uses: "example/action@main"
""",
        encoding="utf-8",
    )

    errors = _check_action_refs(tmp_path)

    assert any("example/action@main" in error for error in errors)


def test_supply_chain_pin_check_rejects_platform_qualified_from(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM --platform=$BUILDPLATFORM python:latest AS builder\n", encoding="utf-8")

    errors = _check_container_refs(tmp_path)

    assert any("python:latest" in error for error in errors)


def test_crap_gate_rejects_empty_function_metrics(tmp_path: Path) -> None:
    source_root = tmp_path / "src" / "pkg"
    source_root.mkdir(parents=True)
    (source_root / "module.py").write_text("def works() -> int:\n    return 1\n", encoding="utf-8")
    coverage = tmp_path / "coverage.json"
    coverage.write_text(json.dumps({"files": {str(source_root / "module.py"): {"functions": {}}}}), encoding="utf-8")

    assert crap_gate_main(["--coverage", str(coverage), "--src", str(source_root)]) == 1


def test_crap_gate_accepts_class_method_coverage_qualnames(tmp_path: Path) -> None:
    source_root = tmp_path / "src" / "pkg"
    source_root.mkdir(parents=True)
    module = source_root / "module.py"
    module.write_text(
        """
class Example:
    def works(self) -> int:
        return 1
""",
        encoding="utf-8",
    )
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps(
            {
                "files": {
                    str(module): {
                        "functions": {
                            "Example.works": {"summary": {"covered_lines": 2, "num_statements": 2}},
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    assert crap_gate_main(["--coverage", str(coverage), "--src", str(source_root)]) == 0


def test_crap_gate_checks_init_file_functions(tmp_path: Path) -> None:
    source_root = tmp_path / "src" / "pkg"
    source_root.mkdir(parents=True)
    init_file = source_root / "__init__.py"
    init_file.write_text("def exported() -> int:\n    return 1\n", encoding="utf-8")
    coverage = tmp_path / "coverage.json"
    coverage.write_text(json.dumps({"files": {str(init_file): {"functions": {}}}}), encoding="utf-8")

    assert crap_gate_main(["--coverage", str(coverage), "--src", str(source_root)]) == 1


def test_mutation_gate_rejects_incomplete_totals(tmp_path: Path) -> None:
    stats = tmp_path / "stats.json"
    stats.write_text(
        json.dumps(
            {
                "total": 10,
                "killed": 1,
                "survived": 0,
                "no_tests": 0,
                "suspicious": 0,
                "timeout": 0,
                "check_was_interrupted_by_user": 0,
                "segfault": 0,
                "not_checked": 0,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="classified mutants"):
        check_mutation_gate(stats)
