# WeStock 实时冒烟测试 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增可直接执行的 Python 冒烟脚本，真实展示 `westock-data` 和 `westock-tool` 的结果并以退出码反映整体状态。

**Architecture:** 脚本独立于 LLM 编排，依据现有 `config.py` 获取 Node 与内置 CLI 的路径。它以固定参数列表调用两个 Node CLI、把命令结果封装为数据类、逐项打印结果，并在所有项目结束后汇总退出码。单元测试替换子进程执行，避免网络依赖。

**Tech Stack:** Python 3.8+ 标准库、`unittest`、`subprocess`、Node.js 内置的 WeStock CLI。

---

## File structure

- Create: `scripts/smoke_test_westock.py` — 固定的实时 WeStock 检查、输出和 CLI 入口。
- Create: `tests/test_smoke_test_westock.py` — 不联网验证命令构造、失败处理与返回码汇总。

### Task 1: 定义冒烟检查的可测试执行单元

**Files:**
- Create: `tests/test_smoke_test_westock.py`
- Create: `scripts/smoke_test_westock.py`

- [ ] **Step 1: 写入失败测试，描述行情检查的 Node 命令**

```python
from pathlib import Path
from unittest.mock import patch

from scripts import smoke_test_westock


def test_run_check_executes_node_cli_with_fixed_arguments():
    completed = smoke_test_westock.subprocess.CompletedProcess(
        args=[], returncode=0, stdout="quote output", stderr=""
    )
    with patch("scripts.smoke_test_westock.subprocess.run", return_value=completed) as run:
        result = smoke_test_westock.run_check(
            "行情",
            Path("/tmp/westock-data.js"),
            ["quote", "sh600519"],
            "node",
        )

    assert result.ok is True
    assert result.stdout == "quote output"
    run.assert_called_once_with(
        ["node", "/tmp/westock-data.js", "quote", "sh600519"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
```

- [ ] **Step 2: 运行测试，确认因模块不存在而失败**

Run: `python -m unittest tests.test_smoke_test_westock -v`

Expected: FAIL，错误指出 `scripts.smoke_test_westock` 不存在。

- [ ] **Step 3: 实现最小执行单元**

```python
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
        return self.returncode == 0


def run_check(name: str, script_path: Path, args: List[str], node_path: str, timeout: int = 30) -> CheckResult:
    command = [node_path, str(script_path), *args]
    started_at = time.perf_counter()
    completed = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", timeout=timeout, check=False
    )
    return CheckResult(name, command, completed.returncode, completed.stdout, completed.stderr,
                       time.perf_counter() - started_at)
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python -m unittest tests.test_smoke_test_westock -v`

Expected: PASS，`test_run_check_executes_node_cli_with_fixed_arguments` 通过。

- [ ] **Step 5: 提交执行单元与测试**

```bash
git add scripts/smoke_test_westock.py tests/test_smoke_test_westock.py
git commit -m "feat(westock): 添加实时冒烟测试脚本"
```

### Task 2: 实现错误处理、固定检查和终端汇总

**Files:**
- Modify: `tests/test_smoke_test_westock.py`
- Modify: `scripts/smoke_test_westock.py`

- [ ] **Step 1: 写入失败测试，描述非零退出与整体失败返回码**

```python
def test_run_check_returns_failure_for_nonzero_exit_code():
    completed = smoke_test_westock.subprocess.CompletedProcess(
        args=[], returncode=2, stdout="", stderr="request rejected"
    )
    with patch("scripts.smoke_test_westock.subprocess.run", return_value=completed):
        result = smoke_test_westock.run_check(
            "选股", Path("/tmp/westock-tool.js"), ["strategy", "macd_golden", "--limit", "5"], "node"
        )

    assert result.ok is False
    assert result.returncode == 2
    assert result.stderr == "request rejected"


def test_main_returns_one_when_one_fixed_check_fails():
    results = [
        smoke_test_westock.CheckResult("行情", ["node"], 0, "ok", "", 0.1),
        smoke_test_westock.CheckResult("选股", ["node"], 1, "", "failed", 0.1),
    ]
    with patch("scripts.smoke_test_westock.run_check", side_effect=results):
        assert smoke_test_westock.main() == 1
```

- [ ] **Step 2: 运行测试，确认 `main` 尚未定义或未返回预期值**

Run: `python -m unittest tests.test_smoke_test_westock -v`

Expected: FAIL，`test_main_returns_one_when_one_fixed_check_fails` 失败。

- [ ] **Step 3: 实现固定检查、异常转换和汇总入口**

```python
def run_check(name: str, script_path: Path, args: List[str], node_path: str, timeout: int = 30) -> CheckResult:
    command = [node_path, str(script_path), *args]
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
        return CheckResult(
            name=name,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_seconds=time.perf_counter() - started_at,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return CheckResult(
            name=name,
            command=command,
            returncode=1,
            stdout="",
            stderr=str(error),
            elapsed_seconds=time.perf_counter() - started_at,
        )


def main() -> int:
    checks = [
        ("行情", config.WESTOCK_DATA_SCRIPT, ["quote", "sh600519"]),
        ("选股", config.WESTOCK_TOOL_SCRIPT, ["strategy", "macd_golden", "--limit", "5"]),
    ]
    results = [run_check(name, Path(script), args, config.NODE_PATH) for name, script, args in checks]
    for result in results:
        print_result(result)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

`print_result` 必须逐项打印名称、`shlex.join(result.command)`、退出码、以秒计的耗时，并只在非空时打印 stdout 与 stderr。

- [ ] **Step 4: 运行单元测试，确认所有测试通过**

Run: `python -m unittest tests.test_smoke_test_westock -v`

Expected: PASS，三个测试全部通过。

- [ ] **Step 5: 执行真实冒烟检查并保留终端结果**

Run: `python scripts/smoke_test_westock.py`

Expected: 两项检查都展示实际输出；命令以 `0` 结束，或以 `1` 结束并明确打印远端/网络/授权错误。

- [ ] **Step 6: 运行完整项目测试集**

Run: `python -m unittest discover -s tests -v`

Expected: 所有可发现的测试通过；若环境尚未安装 `python-dotenv`，先运行项目初始化脚本后重试，并报告依赖问题而非掩盖失败。

- [ ] **Step 7: 提交汇总功能与测试**

```bash
git add scripts/smoke_test_westock.py tests/test_smoke_test_westock.py
git commit -m "test(westock): 覆盖冒烟检查失败场景"
```
