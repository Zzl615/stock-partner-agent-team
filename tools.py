import subprocess
import shlex
import os
import sys
import config

def execute_node_script(script_path, args_str):
    """
    Executes a Node.js script with the given arguments.
    Returns the stdout as markdown string, or error message on failure.
    """
    try:
        # Split command line arguments respecting quotes
        args = shlex.split(args_str)
        cmd = [config.NODE_PATH, script_path] + args
        
        # Run subprocess
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        
        if result.returncode != 0:
            err_msg = result.stderr.strip()
            print(f"Error running Node script {os.path.basename(script_path)}: {err_msg}", file=sys.stderr)
            return f"**Error executing tool:**\n```\n{err_msg}\n```"
            
        return result.stdout
    except Exception as e:
        print(f"Exception running Node script {os.path.basename(script_path)}: {e}", file=sys.stderr)
        return f"**Exception executing tool:**\n```\n{e}\n```"

def query_westock_data(command: str) -> str:
    """
    Query stock quotes, financials, or macro data using westock-data.
    E.g., query_westock_data("quote sh600519") or query_westock_data("finance sh600519 --num 4")
    """
    print(f"[Tool Call] westock-data {command}")
    return execute_node_script(config.WESTOCK_DATA_SCRIPT, command)

def query_westock_tool(command: str) -> str:
    """
    Query stock filtering or screening results using westock-tool.
    E.g., query_westock_tool("strategy macd_golden") or query_westock_tool("filter --preset LowPE")
    """
    print(f"[Tool Call] westock-tool {command}")
    return execute_node_script(config.WESTOCK_TOOL_SCRIPT, command)

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
