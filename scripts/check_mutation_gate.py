import json
import sys
from pathlib import Path
from typing import cast

BLOCKING_FIELDS = (
    "survived",
    "no_tests",
    "suspicious",
    "timeout",
    "check_was_interrupted_by_user",
    "segfault",
)


def _read_stats(path: Path) -> dict[str, int]:
    raw_data = cast("object", json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(raw_data, dict):
        raise SystemExit(f"mutation stats must be a JSON object: {path}")

    return {key: value for key, value in raw_data.items() if isinstance(key, str) and isinstance(value, int)}


def _format_blockers(stats: dict[str, int]) -> str:
    blockers = [f"{field}={stats.get(field, 0)}" for field in BLOCKING_FIELDS if stats.get(field, 0) > 0]
    return ", ".join(blockers)


def check_mutation_gate(path: Path) -> int:
    stats = _read_stats(path)
    blockers = _format_blockers(stats)
    total = stats.get("total", 0)

    if blockers:
        print(f"mutation gate failed: {blockers}", file=sys.stderr)
        return 1

    print(f"mutation gate passed: total={total}, killed={stats.get('killed', 0)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m scripts.check_mutation_gate <mutmut-cicd-stats.json>", file=sys.stderr)
        return 2

    return check_mutation_gate(Path(args[0]))


if __name__ == "__main__":
    raise SystemExit(main())
