# WeStock 实时冒烟测试设计

## 目标

提供一个不经 LLM 编排的 Python 命令行脚本，实际调用本项目内置的 `westock-data` 与 `westock-tool`，让开发者可以直接看到两个工具的业务输出并判断调用是否成功。

## 范围

- 调用 `westock-data quote sh600519`，验证公共个股行情查询。
- 调用 `westock-tool strategy macd_golden --limit 5`，验证预置策略选股。
- 输出每个命令的名称、完整命令、退出码、耗时、标准输出和标准错误。
- 任一命令失败时，脚本最终以退出码 `1` 结束，但仍展示另一项的结果。
- 不调用 LLM，不写入报告或数据，不接收任意 shell 命令。

## 设计

新增 `scripts/smoke_test_westock.py`，将 Python 解释器无关的 Node 调用封装为 `run_check(name, script_path, args, node_path)`。默认路径从现有 `config.py` 获取，确保与应用运行时使用相同的 Node 路径和内置 CLI 文件。

脚本以固定的、参数列表形式的命令执行，禁止 shell 拼接；每项结果在终端按清晰分段打印。命令执行超时、Node 不存在、CLI 非零退出均转换为结构化失败结果，不中断后续检查。

## 测试

新增单元测试，以替换 `subprocess.run` 的方式验证：

1. 行情检查使用预期的 Node 命令与参数。
2. 非零退出码被报告为失败。
3. 汇总逻辑在任一检查失败时返回 `1`，全部成功时返回 `0`。

单元测试不访问网络；实际行情与策略结果由手动运行冒烟脚本验证。
