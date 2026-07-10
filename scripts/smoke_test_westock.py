import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

# When invoked as ``python scripts/smoke_test_westock.py``, Python puts only
# the scripts directory on ``sys.path``. Add the project root so the shared
# config module remains importable; module/test invocation already has it.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


@dataclass
class CheckResult:
    name: str
    command: List[str]
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float

    @property
    def ok(self) -> bool:
        if self.returncode != 0:
            return False
        output = f"{self.stdout}\n{self.stderr}"
        return "SKILL_006" not in output and "执行失败" not in output


def run_check(
    name: str,
    script_path: Path,
    args: List[str],
    node_path: str,
    timeout: int = 30,
) -> CheckResult:
    command = [node_path, str(script_path)] + args
    started_at = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return CheckResult(
            name=name,
            command=command,
            returncode=1,
            stdout="",
            stderr=str(error),
            elapsed_seconds=time.perf_counter() - started_at,
        )

    elapsed_seconds = time.perf_counter() - started_at

    return CheckResult(
        name=name,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        elapsed_seconds=elapsed_seconds,
    )


def print_result(result: CheckResult) -> None:
    print(f"检查: {result.name}")
    print(f"命令: {shlex.join(result.command)}")
    print(f"退出码: {result.returncode}")
    print(f"耗时: {result.elapsed_seconds:.2f} 秒")
    print(f"stdout:\n{result.stdout}")
    print(f"stderr:\n{result.stderr}")


def main() -> int:
    checks = [
        ("行情", config.WESTOCK_DATA_SCRIPT, ["quote", "sh600519"]),
        ("选股", config.WESTOCK_TOOL_SCRIPT, ["strategy", "macd_golden", "--limit", "5"]),
    ]
    results = []
    for name, script_path, args in checks:
        result = run_check(name, Path(script_path), args, config.NODE_PATH)
        results.append(result)
        print_result(result)

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
