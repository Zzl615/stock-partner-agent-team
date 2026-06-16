# Stock-Partner Multi-Agent Roundtable Team (Python Standalone Project)

This project is a standalone Python port of the **Stock-Partner Roundtable Expert Team** (自选股投研圆桌专家团) extracted from WorkBuddy. It orchestrates a group of 6 expert sub-agents to analyze A-shares, Hong Kong shares, and US stocks, producing high-fidelity markdown and HTML roundtable analysis reports.

---

## 1. Project Directory Structure

* `main.py`: Command Line Interface entrypoint.
* `orchestrator.py`: Orchestrator that parses stock codes, spawns sub-agents in parallel, and consolidates findings.
* `llm.py`: Unified LLM wrapper supporting OpenAI SDK (compatible with Gemini & OpenAI APIs) and native Gemini SDK.
* `tools.py`: Python wrapper to execute the Node.js quantitative stock CLIs.
* `config.py`: Configuration and environment loader.
* `agents/`: Directory containing prompt files for all 7 agents.
* `skills/`: Local copy of `westock-data`, `westock-tool` (Node.js) and `md-to-html` (report renderer).
* `avatars/`: Avatar images for report rendering.
* `templates/`: Config templates containing past analysis query configs.

---

## 2. Environment Setup

### 2.1. Prerequisites
- **Python**: Version 3.8+ (Recommend Python 3.10+)
- **Node.js**: Version 18+ (Required for quantitative data tools)

### 2.2. Installation Steps
1. Create a Python Virtual Environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install Python Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up configuration:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and fill in your API keys (e.g., `GEMINI_API_KEY` or `OPENAI_API_KEY`).

---

## 3. Usage & CLI Examples

### 3.1. List Available Templates
Run with `--list-templates` to view pre-defined historical session configurations (from teams history):
```bash
python main.py --list-templates
```

### 3.2. Run a New Stock Analysis
Analyze a specific stock by providing a custom query and stock code:
```bash
python main.py --query "分析贵州茅台走势与买入时机" --code sh600519
```

### 3.3. Run using a Template
Run using one of the migrated roundtable templates (e.g. A-share hot sectors, portfolio holdings, or STAR 50 index timing):
```bash
# Run using the portfolio analysis roundtable template (Task 2)
python main.py --template stock-partner-roundtable

# Run using the STAR 50 timing template (Task 7)
python main.py --template stock-partner-roundtable-0525
```

### 3.4. Target Sub-agents Selection
By default, all 6 sub-agents will run. To run only specific agents to save costs or time, use `--agents`:
```bash
python main.py --query "分析贵州茅台" --code sh600519 --agents "valuation-analyst,signal-chief"
```

---

## 4. Reports Output
The orchestrator automatically outputs reports to the `./output/<YYYY-MM-DD>/` directory:
1. **Individual Expert Reports**: `<Stock>-<Expert Title>.md` (e.g., `sh600519-估值分析师.md`)
2. **Consolidated Roundtable Report**: `<Stock>-圆桌报告.md` (Markdown format)
3. **High-Fidelity HTML Report**: `<Stock>-圆桌报告.html` (Rendered with styles and embedded avatars for sharing)
