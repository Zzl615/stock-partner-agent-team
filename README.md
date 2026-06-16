# Stock-Partner Multi-Agent Roundtable Team (Python Standalone Project)

This project is a standalone Python implementation of the **Tencent Stock-Partner Roundtable Expert Team** (自选股投研圆桌专家团) extracted and decoupled from WorkBuddy. It orchestrates a team of 6 expert sub-agents with different investment perspectives for collaborative stock analysis, producing professional multi-perspective markdown reports and high-fidelity, visually rich HTML reports.

*Note: For the Chinese version of this documentation, please see [README_zh.md](README_zh.md).*

---

## 1. Project Architecture

The architecture is designed as follows with modular separation of concerns:

* **Core Orchestration & Interfaces (Python)**:
  * `main.py`: CLI entrypoint. Supports direct queries and stock code inputs, as well as template-based execution via `--template`.
  * `orchestrator.py`: The team orchestration engine. Employs `ThreadPoolExecutor` to run the 6 sub-agents' ReAct loops in parallel, aggregates their reports, and leverages the Roundtable Lead (Research Editor) to consolidate findings into a final roundtable report.
  * `llm.py`: Unified LLM client. Implements a ReAct loop to intercept and execute tools called by the agents. Fully compatible with **Gemini API** (supports native SDK and OpenAI-compatible endpoint) and **OpenAI API**.
  * `tools.py`: Tool execution wrapper. Converts Node.js scripts into Python callable functions executed via `subprocess`.
  * `config.py`: Core configuration and path loader.
* **Decoupled Assets**:
  * `agents/`: Decoupled prompt files for all 7 agents:
    * `stock-partner-lead` (Roundtable Lead / Research Editor)
    * `industry-strategist` (Industry Strategist)
    * `signal-chief` (Signal Chief)
    * `valuation-analyst` (Valuation Analyst)
    * `contrarian-investor` (Contrarian Investor)
    * `fundamental-researcher` (Fundamental Researcher)
    * `shortterm-surfer` (Shortterm Surfer)
  * `skills/`:
    * `westock-data` & `westock-tool`: A self-contained Node.js client (with its own `node_modules` environment) offering A-share, HK-share, and US stock real-time quotes, K-lines, financials, and 40+ quantitative strategy filters.
    * `md-to-html`: Visual HTML report renderer containing `shell.html`, styling rules, and Python scripts to embed images and assemble reports.
  * `avatars/`: Avatar images for all analysts.
  * `templates/`: Config templates for 3 historical roundtables containing inbox messages and task contexts.

---

## 2. Environment Setup

### 2.1. Prerequisites
- **Python** >= 3.8 (Recommend Python 3.10+)
- **Node.js** >= 18 (Required for quantitative skills)

### 2.2. One-click Installation
Run the automated setup script in your terminal:
```bash
./setup.sh
```
This script will:
1. Initialize a Python virtual environment (`.venv`).
2. Install Python dependencies (`google-generativeai`, `openai`, `pandas`, etc.).
3. Install Node dependencies for stock-market tools.
4. Copy `.env.example` to `.env` if not already present.

---

## 3. Configuration & Execution Guide

### 3.1. Configure API Keys
Edit the `.env` file in the root directory to set your provider and API key (Gemini is the default):
```ini
LLM_PROVIDER=gemini

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# For OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_MODEL=gpt-4o
```

### 3.2. Running the Roundtable

First, activate the virtual environment:
```bash
source .venv/bin/activate
```

#### Option A: Run Using Historical Templates (Recommended for Testing)
List all available templates:
```bash
python main.py --list-templates
```
Run using a specific template:
```bash
python main.py --template stock-partner-roundtable-2
```

#### Option B: Start a New Analysis Query
Provide custom analysis query text and stock ticker codes:
```bash
python main.py --query "Analyze the latest trend for CATL and BYD" --code 300750,sz002594
```

#### Option C: Activate Specific Agents (Save Token/Cost)
If you only care about valuation and signals, run with selected sub-agents:
```bash
python main.py --query "Analyze BYD" --code sz002594 --agents "valuation-analyst,signal-chief"
```

---

## 4. Reports Output

After a successful run, reports will be archived under the `./output/<YYYY-MM-DD>/` directory:
1. **Individual Expert Reports**: Named as `<Symbol>-<Role>.md` (e.g., `300750-估值分析师.md`).
2. **Roundtable Consensus Report**: Gathers findings into `<Symbol>-圆桌报告.md`.
3. **High-Fidelity Visual HTML Report**: `<Symbol>-圆桌报告.html` (Complete, self-contained report containing styles and embedded base64 avatars, ready to view in any browser).
