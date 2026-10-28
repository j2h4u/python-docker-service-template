"""Manual offline audit, with explicitly authorized native HTTP embeddings."""

import argparse
import ipaddress
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

from scripts.clone_tools import inventory, parse_jscpd


class AuditArgs(argparse.Namespace):
    semantic: bool
    endpoint: str | None
    model: str | None
    include_tests: bool
    timeout: float
    output: Path
    roots: tuple[str, ...]


def _endpoint(value: str) -> str:
    parsed = urlsplit(value)
    host = parsed.hostname or ""
    loopback = host == "localhost"
    with suppress(ValueError):
        loopback = loopback or ipaddress.ip_address(host).is_loopback
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("endpoint must not contain credentials, query or fragment")
    if not host or (parsed.scheme != "https" and not (parsed.scheme == "http" and loopback)):
        raise ValueError("endpoint requires HTTPS (HTTP allowed only on loopback)")
    return value


def _run(command: list[str], root: Path, deadline: float, env: dict[str, str]) -> str:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("total audit deadline exceeded")
    with subprocess.Popen(
        command,
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    ) as process:
        try:
            output, _ = process.communicate(timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise TimeoutError("total audit deadline exceeded") from None
        key = env.get("JSCPD_SEMANTIC_API_KEY", "")
        if key:
            output = output.replace(key, "[redacted]")
        if process.returncode:
            raise RuntimeError(f"detector exited {process.returncode}: {output}")
        return output


def _semantic(args: AuditArgs, root: Path, run: Path, deadline: float) -> None:
    assert args.endpoint is not None and args.model is not None
    output = run / "semantic"
    output.mkdir()
    config = output / "config.json"
    config.write_text("{}", encoding="utf-8")
    sources = inventory(root, args.roots)
    if not sources:
        return
    env = dict(os.environ, JSCPD_CACHE_DIR=str(args.output.resolve() / "cache"))
    command = [
        "jscpd",
        "--config",
        str(config),
        "--semantic",
        "--semantic-provider",
        "http",
        "--semantic-url",
        args.endpoint,
        "--semantic-model",
        args.model,
        "--kind",
        "semantic",
        "--format",
        "python",
        "--no-gitignore",
        "--absolute",
        "--min-tokens",
        "1",
        "--min-lines",
        "1",
        "--reporters",
        "json",
        "--output",
        str(output),
        *sources,
    ]
    log = _run(command, root, deadline, env)
    (output / "detector.log").write_text(log, encoding="utf-8")
    report = cast("object", json.loads((output / "jscpd-report.json").read_text(encoding="utf-8")))
    if not isinstance(report, dict) or not isinstance(report.get("duplicates"), list):
        raise ValueError("invalid semantic report")
    parse_jscpd(report, root, sources)
    if "error" in log.lower() or "skipp" in log.lower():
        raise ValueError("semantic detector reported errors or skipped input")


def _arguments(argv: list[str] | None) -> AuditArgs:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semantic", action="store_true")
    parser.add_argument("--endpoint")
    parser.add_argument("--model")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--output", type=Path, default=Path(".clone-audit"))
    args = parser.parse_args(argv, namespace=AuditArgs())
    args.roots = ("src", "scripts", "tests") if args.include_tests else ("src", "scripts")
    return args


def _validate(args: AuditArgs) -> None:
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if args.semantic:
        if not args.endpoint or not args.model or not os.environ.get("JSCPD_SEMANTIC_API_KEY"):
            raise ValueError("semantic requires explicit endpoint, model and JSCPD_SEMANTIC_API_KEY")
        _endpoint(args.endpoint)
    elif args.endpoint or args.model:
        raise ValueError("endpoint/model require --semantic")


def main(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="run-", dir=args.output))
    temporary = run / "temporary"
    temporary.mkdir()
    report: dict[str, object] = {
        "state": "failed",
        "run": str(run),
        "scope": list(args.roots),
        "semantic": args.semantic,
        "endpoint": None,
        "model": args.model,
        "timeout_seconds": args.timeout,
        "errors": [],
        "limits": {
            "native_http_batch_functions": 32,
            "native_http_batch_bytes_soft": 65536,
            "native_http_retries": 3,
            "request_quota": "not supported",
            "model_reproducibility": "model aliases are not pinned",
            "cache": "native endpoint/model/request-shape/preprocessing/content identity",
        },
    }
    try:
        _validate(args)
        report["endpoint"] = args.endpoint
        deadline = time.monotonic() + args.timeout
        command = [
            sys.executable,
            "-c",
            (
                "import sys; from pathlib import Path; from scripts.clone_tools import analyze; "
                "analyze(Path.cwd(), tuple(sys.argv[2:]), Path(sys.argv[1]))"
            ),
            str(run / "offline"),
            *args.roots,
        ]
        _run(command, Path.cwd(), deadline, dict(os.environ, TMPDIR=str(temporary)))
        report["state"] = "incomplete"
        if args.semantic:
            _semantic(args, Path.cwd(), run, deadline)
        report["state"] = "complete"
    except (OSError, ValueError, RuntimeError, TimeoutError, KeyError, TypeError, SyntaxError) as error:
        key = os.environ.get("JSCPD_SEMANTIC_API_KEY", "")
        report["errors"] = [str(error).replace(key, "[redacted]") if key else str(error)]
    finally:
        shutil.rmtree(temporary)
    (args.output / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"clone audit {report['state']}", file=sys.stderr)
    return 0 if report["state"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
