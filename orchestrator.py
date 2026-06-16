import os
import sys
import re
import datetime
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import config
import llm
import tools

# Agents metadata mapping
AGENT_METADATA = {
    "industry-strategist": {
        "name": "industry-strategist",
        "title": "产业策略师",
        "prompt_file": "industry-strategist.md"
    },
    "signal-chief": {
        "name": "signal-chief",
        "title": "信号派首席",
        "prompt_file": "signal-chief.md"
    },
    "valuation-analyst": {
        "name": "valuation-analyst",
        "title": "估值分析师",
        "prompt_file": "valuation-analyst.md"
    },
    "contrarian-investor": {
        "name": "contrarian-investor",
        "title": "逆向投资人",
        "prompt_file": "contrarian-investor.md"
    },
    "fundamental-researcher": {
        "name": "fundamental-researcher",
        "title": "财报研究员",
        "prompt_file": "fundamental-researcher.md"
    },
    "shortterm-surfer": {
        "name": "shortterm-surfer",
        "title": "短线冲浪手",
        "prompt_file": "shortterm-surfer.md"
    },
    "stock-partner-lead": {
        "name": "stock-partner-lead",
        "title": "投研主编",
        "prompt_file": "stock-partner-lead.md"
    }
}

def load_agent_prompt(agent_id):
    """
    Loads agent prompt from its markdown file, stripping frontmatter.
    """
    meta = AGENT_METADATA.get(agent_id)
    if not meta:
        raise ValueError(f"Unknown agent ID: {agent_id}")
        
    prompt_path = os.path.join(config.AGENTS_DIR, meta["prompt_file"])
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Agent prompt file not found at: {prompt_path}")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Strip YAML frontmatter if present
    content = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
    return content.strip()

def extract_stock_codes(query):
    """
    Tries to search for stock codes in the query.
    If none found, returns None.
    Supports formats like sh600519, 000001.SZ, 600150, hk00700, US.AAPL etc.
    """
    # Simple regex to capture stock tickers/codes
    codes = re.findall(r"\b(?:sh|sz|hk|bj|us)?\.?\d{5,6}\b|\b(?:us\.)?[A-Z]{2,5}\b", query, re.IGNORECASE)
    cleaned_codes = []
    for code in codes:
        # Normalize code format if needed (e.g. sh600519 or US.AAPL)
        cleaned_codes.append(code.upper())
    return list(set(cleaned_codes)) if cleaned_codes else None

def run_sub_agent(agent_id, user_query, stock_codes=None):
    """
    Runs a single sub-agent on the query and returns its report.
    """
    meta = AGENT_METADATA[agent_id]
    prompt = load_agent_prompt(agent_id)
    
    # Customize the task context
    stock_context = f"涉及股票代码: {', '.join(stock_codes)}" if stock_codes else "无特定股票代码"
    task_prompt = f"""
用户问题: {user_query}
{stock_context}
工具优先级: 数据查询/个股详情优先用 `westock-data` (例如: quote, finance, kline)，选股/筛选/策略/标签优先用 `westock-tool`。
产出方式: 请基于您的专业研究框架，输出一篇详实的分析报告。您的报告必须用 markdown 格式，字数不少于800字。字里行间保持您的专业人设和文风特点。
"""
    
    report = llm.run_agent(meta["title"], prompt, task_prompt)
    return agent_id, report

def run_roundtable_lead(user_query, sub_reports, stock_codes=None):
    """
    Runs the lead agent to consolidate sub-reports into a roundtable report.
    Returns the final markdown report and the body HTML segment.
    """
    lead_meta = AGENT_METADATA["stock-partner-lead"]
    lead_prompt = load_agent_prompt("stock-partner-lead")
    
    # Format sub-reports for consolidation
    reports_text = ""
    for agent_id, report in sub_reports.items():
        title = AGENT_METADATA[agent_id]["title"]
        reports_text += f"\n\n=========================================\n"
        reports_text += f"【{title}】的独立分析报告:\n"
        reports_text += f"=========================================\n\n"
        reports_text += report
        
    task_prompt = f"""
用户原问题: {user_query}
涉及股票代码: {', '.join(stock_codes) if stock_codes else '无'}

这里是投研圆桌团队所有上场专家的独立分析报告:
{reports_text}

请根据您的主理人（投研主编）职责，将这些专家的观点与数据整合汇编，输出最终的《自选股金融分析圆桌报告》。

您的输出必须同时包含以下两个部分，用特殊的标记隔开：

---START_MARKDOWN_REPORT---
（此处写符合 4 模块结构的完整 Markdown 圆桌报告，章节包括：
01 结论卡
02 子专家观点
03 深度思考
04 后续关注
字数必须不少于上场成员报告总字数的 70%）
---END_MARKDOWN_REPORT---

---START_BODY_HTML---
（此处输出符合圆桌 HTML 规范的 body.html 片段，仅包含 nav, hero, snapshot, voice-stack, passage-card 等 body 级 HTML 块，不包含 <!DOCTYPE>, <html>, <head>, <body> 标签，这将在稍后套进 shell.html 模板中。请确保 class 类名与头像映射完全匹配。）
---END_BODY_HTML---
"""
    
    lead_output = llm.run_agent(lead_meta["title"], lead_prompt, task_prompt)
    
    # Parse markdown and html parts from lead output
    md_report = ""
    body_html = ""
    
    md_match = re.search(r"---START_MARKDOWN_REPORT---(.*?)---END_MARKDOWN_REPORT---", lead_output, re.DOTALL)
    html_match = re.search(r"---START_BODY_HTML---(.*?)---END_BODY_HTML---", lead_output, re.DOTALL)
    
    if md_match:
        md_report = md_match.group(1).strip()
    else:
        # Fallback if tags are missing
        md_report = lead_output
        
    if html_match:
        body_html = html_match.group(1).strip()
        # Clean up any wrapping code blocks like ```html ... ```
        body_html = re.sub(r"^```html\s*\n", "", body_html)
        body_html = re.sub(r"\n```$", "", body_html)
        
    return md_report, body_html

def run_team_roundtable(user_query, active_agents=None, output_dir=None):
    """
    Orchestrates the entire roundtable team.
    """
    if not active_agents:
        # Default to all 6 experts
        active_agents = [
            "industry-strategist",
            "signal-chief",
            "valuation-analyst",
            "contrarian-investor",
            "fundamental-researcher",
            "shortterm-surfer"
        ]
        
    print(f"[*] Starting roundtable orchestration...")
    print(f"[*] Query: {user_query}")
    
    stock_codes = extract_stock_codes(user_query)
    print(f"[*] Detected stock codes: {stock_codes}")
    
    # 1. Spawn sub-agents in parallel using thread pool
    sub_reports = {}
    print(f"[*] Spawning {len(active_agents)} sub-agents in parallel...")
    with ThreadPoolExecutor(max_workers=len(active_agents)) as executor:
        futures = {executor.submit(run_sub_agent, aid, user_query, stock_codes): aid for aid in active_agents}
        for future in as_completed(futures):
            aid = futures[future]
            try:
                agent_id, report = future.result()
                sub_reports[agent_id] = report
                print(f"[✓] Agent '{aid}' completed analysis.")
            except Exception as e:
                print(f"[✗] Agent '{aid}' failed: {e}", file=sys.stderr)
                
    # 2. Consolidate reports via lead agent
    print(f"[*] Consolidating reports via Roundtable Lead...")
    md_report, body_html = run_roundtable_lead(user_query, sub_reports, stock_codes)
    
    # 3. Handle outputs
    date_str = datetime.date.today().isoformat()
    theme = "A股研报"
    if stock_codes:
        theme = stock_codes[0]
    
    # Determine directory
    if not output_dir:
        output_dir = os.path.join(config.project_root, "output", date_str)
    os.makedirs(output_dir, exist_ok=True)
    
    # Save individual reports
    for aid, report in sub_reports.items():
        title = AGENT_METADATA[aid]["title"]
        fpath = os.path.join(output_dir, f"{theme}-{title}.md")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[✓] Saved sub-agent report: {fpath}")
        
    # Save lead markdown report
    md_fpath = os.path.join(output_dir, f"{theme}-圆桌报告.md")
    with open(md_fpath, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"[✓] Saved lead markdown report: {md_fpath}")
    
    # Render and save HTML report if body html was generated
    html_fpath = os.path.join(output_dir, f"{theme}-圆桌报告.html")
    if body_html:
        body_fpath = os.path.join(output_dir, f"{theme}-圆桌报告.body.html")
        with open(body_fpath, "w", encoding="utf-8") as f:
            f.write(body_html)
            
        print(f"[*] Rendering HTML report using render.py...")
        # Run subprocess to execute render.py
        # E.g. python3 render.py <body_file> <output_html> --title="A股指数ETF+科创50" --date=YYYY-MM-DD
        render_script = os.path.join(config.SKILLS_DIR, "md-to-html", "scripts", "render.py")
        cmd = [
            sys.executable,
            render_script,
            body_fpath,
            html_fpath,
            f"--title={theme}自选股投研圆桌报告",
            f"--date={date_str}"
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        if result.returncode == 0:
            print(f"[✓] Saved HTML report: {html_fpath}")
        else:
            print(f"[✗] Failed to render HTML report: {result.stderr}", file=sys.stderr)
    else:
        print("[!] Warning: Lead agent did not output start/end tags for body HTML. Skipping HTML rendering.")
        
    return {
        "output_dir": output_dir,
        "md_report": md_fpath,
        "html_report": html_fpath if body_html else None,
        "sub_reports": sub_reports
    }
