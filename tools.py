import subprocess
import shlex
import os
import sys
import time
import config

def normalize_stock_code(code: str) -> str:
    lowered = code.lower()
    if lowered.startswith(("sh", "sz", "hk", "bj", "us")):
        return code
    if code.isdigit() and len(code) == 6:
        if code.startswith(("6", "5", "9")):
            return f"sh{code}"
        if code.startswith(("0", "1", "2", "3")):
            return f"sz{code}"
    return code

def normalize_westock_data_command(command: str) -> str:
    """
    Normalize common LLM-generated shorthand into supported westock-data CLI syntax.
    """
    args = shlex.split(command)
    if not args:
        return command

    normalized = list(args)
    if normalized[0] == "fund":
        normalized[0] = "asfund"
        if len(normalized) > 1:
            normalized[1] = normalize_stock_code(normalized[1])

    if normalized[0] == "kline" and len(normalized) >= 5 and not normalized[2].startswith("--"):
        normalized = [
            normalized[0],
            normalize_stock_code(normalized[1]),
            "--period",
            normalized[2],
            "--limit",
            normalized[3],
            "--fq",
            normalized[4],
            *normalized[5:],
        ]

    if normalized[0] == "finance" and len(normalized) == 3 and normalized[2].isdigit():
        normalized = [normalized[0], normalize_stock_code(normalized[1]), "--num", normalized[2]]

    if normalized[0] == "technical" and len(normalized) == 3 and not normalized[2].startswith("--"):
        normalized = [normalized[0], normalize_stock_code(normalized[1]), "--group", normalized[2]]

    return shlex.join(normalized)

def execute_node_script(script_path, args_str, tool_name=None):
    """
    Executes a Node.js script with the given arguments.
    Returns the stdout as markdown string, or error message on failure.
    """
    label = tool_name or os.path.basename(script_path)
    started_at = time.perf_counter()
    try:
        # Split command line arguments respecting quotes
        args = shlex.split(args_str)
        cmd = [config.NODE_PATH, script_path] + args
        print(f"[Tool Exec] {label}: {' '.join(shlex.quote(part) for part in cmd)}")
        
        # Run subprocess
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        stdout_len = len(result.stdout or "")
        stderr_len = len(result.stderr or "")
        print(
            f"[Tool Result] {label}: returncode={result.returncode}, elapsed_ms={elapsed_ms}, "
            f"stdout_chars={stdout_len}, stderr_chars={stderr_len}"
        )
        
        if result.returncode != 0:
            err_msg = result.stderr.strip()
            print(f"[Tool Error] {label}: {err_msg}", file=sys.stderr)
            return f"**Error executing tool:**\n```\n{err_msg}\n```"
            
        return result.stdout
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        print(f"[Tool Exception] {label}: elapsed_ms={elapsed_ms}, error={e}", file=sys.stderr)
        return f"**Exception executing tool:**\n```\n{e}\n```"

def query_westock_data(command: str) -> str:
    """
    Query stock quotes, financials, or macro data using westock-data.
    E.g., query_westock_data("quote sh600519") or query_westock_data("finance sh600519 --num 4")
    """
    normalized_command = normalize_westock_data_command(command)
    if normalized_command != command:
        print(f"[Tool Normalize] westock-data: {command} -> {normalized_command}")
    print(f"[Tool Call] westock-data {normalized_command}")
    return execute_node_script(config.WESTOCK_DATA_SCRIPT, normalized_command, tool_name="westock-data")

def query_westock_tool(command: str) -> str:
    """
    Query stock filtering or screening results using westock-tool.
    E.g., query_westock_tool("strategy macd_golden") or query_westock_tool("filter --preset LowPE")
    """
    print(f"[Tool Call] westock-tool {command}")
    return execute_node_script(config.WESTOCK_TOOL_SCRIPT, command, tool_name="westock-tool")

def render_html_report(md_file_path: str, html_file_path: str, title: str, date_str: str) -> bool:
    """
    Renders a markdown roundtable report into an HTML file using the local render.py script.
    """
    try:
        # Run python render.py <md_file_path> <html_file_path> --title <title> --date <date_str>
        # Note: render.py in md-to-html script takes a body file, or can render markdown.
        # Let's check how the script works. Usually it takes a body.html and builds shell.html.
        # But wait! In stock-partner-lead.md:
        # "跑 render.py: python3 plugins/stock-partner-team/skills/md-to-html/scripts/render.py <body 文件> <最终 HTML> --title="..." --date=YYYY-MM-DD"
        # It expects a body HTML file, not a raw markdown file!
        # Wait, how is the body HTML file generated?
        # In stock-partner-lead.md:
        # "写 body 片段 <主题>-圆桌报告.body.html：含 nav + hero + 4 模块"
        # "圆桌 md 写完后默认调 skills/md-to-html 的 render.py 产出 HTML"
        # Ah! Let's check the contents of render.py to see how it works!
        pass
    except Exception as e:
        print(f"Error rendering HTML: {e}", file=sys.stderr)
        return False
