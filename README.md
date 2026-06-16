# Stock-Partner Multi-Agent Roundtable Team (Python 独立运行项目)

本项目是基于 WorkBuddy 的 **腾讯自选股股票投研专家团** 编排机制提取并独立封装的 Python 智能体团队项目。它通过并发调度 6 位不同投资维度的投研专家进行圆桌会商，提供专业的多视角个股/板块分析报告，并输出高保真的可视化 HTML 研报。

---

## 1. 项目架构说明 (Project Architecture)

整个项目的架构设计如下，各模块职责分工明确：

* **核心调度与接口 (Python)**：
  * `main.py`：命令行入口。支持直接输入查询问题或股票代码，也支持通过 `--template` 指定预设的历史圆桌配置一键运行。
  * `orchestrator.py`：团队会商调度核心。利用 Python `ThreadPoolExecutor` 并发拉起 6 位子专家的 ReAct 循环进行分析，汇总各专家 Markdown 报告后，交由投研主编（主理人）进行共识、分歧提炼，产出圆桌综合报告。
  * `llm.py`：统一大模型客户端。封装了 ReAct 工具调用循环（ReAct Loop），能够自动解析并响应智能体的工具调用请求；全面兼容 **Gemini API**（支持 native SDK 与 OpenAI 兼容接口）以及 **OpenAI API**。
  * `tools.py`：工具执行封装。将 Node.js 命令转化为 Python 调用函数，通过 `subprocess` 执行底层的行情与选股 CLI 工具。
  * `config.py`：配置及路径管理中心。
* **迁移资产 (Assets)**：
  * `agents/`：从 `.workbuddy` 系统迁移出来的 7 位专家角色的核心 Prompt 定义库：
    * `stock-partner-lead` (圆汇众 · 投研主编)
    * `industry-strategist` (星望远 · 产业策略师)
    * `signal-chief` (洲四方 · 信号派首席)
    * `valuation-analyst` (文衡价 · 估值分析师)
    * `contrarian-investor` (坤候底 · 逆向投资人)
    * `fundamental-researcher` (钊审财 · 财报研究员)
    * `shortterm-surfer` (磊追浪 · 短线冲浪手)
  * `skills/`：
    * `westock-data` 与 `westock-tool`：包含了自选股实时行情、分时、K线、财务数据查询以及 40+ 预置选股策略的 Node.js 客户端（独立包含了 node_modules 运行环境）。
    * `md-to-html`：包含可视化报告渲染外壳 `shell.html`、CSS 样式规范，以及 Python 合成与头像内嵌脚本。
  * `avatars/`：圆桌主理人及 6 位专家的图片头像。
  * `templates/`：备份自飞书/WorkBuddy 会商历史的 3 个典型圆桌任务模板，包含了对应的成员 inbox 信息与任务上下文。

---

## 2. 环境配置与安装 (Environment Setup)

### 2.1. 依赖要求
- **Python** >= 3.8 (推荐 Python 3.10+)
- **Node.js** >= 18 (数据查询工具运行所需)

### 2.2. 一键安装
项目内置了自动化的安装脚本，在终端中进入项目目录直接执行即可：
```bash
./setup.sh
```
该脚本会自动：
1. 创建 Python 虚拟环境 `.venv`。
2. 激活虚拟环境并安装 Python 依赖（`google-generativeai`、`openai`、`pandas` 等）。
3. 安装 Node.js 行情工具依赖。
4. 基于 `.env.example` 生成 `.env` 配置文件。

---

## 3. 配置与运行指南 (Configuration & Running)

### 3.1. 填写大模型密钥
请使用编辑器打开根目录下的 `.env` 文件，并根据您使用的 LLM 厂商填写 API 密钥（默认首选 Gemini）：
```ini
LLM_PROVIDER=gemini

# API Keys
GEMINI_API_KEY=您的Gemini_API_Key
GEMINI_MODEL=gemini-1.5-pro

# 如果使用 OpenAI，请配置如下：
# LLM_PROVIDER=openai
# OPENAI_API_KEY=您的OpenAI_API_Key
# OPENAI_MODEL=gpt-4o
```

### 3.2. 运行会商服务

首先请确保处于 Python 虚拟环境中：
```bash
source .venv/bin/activate
```

#### 选项 A：使用历史会商模板运行 (推荐测试)
查看所有可用的历史任务模板：
```bash
python main.py --list-templates
```
使用特定的模板一键运行投研分析（例如运行持仓组合诊断）：
```bash
python main.py --template stock-partner-roundtable-2
```

#### 选项 B：全新发起个股/板块分析
提供您关注的问题和股票代码：
```bash
python main.py --query "分析中国船舶与宁德时代的最新走势" --code 600150,300750
```

#### 选项 C：指定专家上场（节省 Token 流量）
如果您只关心估值与资金，可以通过 `--agents` 仅激活特定分析师：
```bash
python main.py --query "分析中国船舶" --code 600150 --agents "valuation-analyst,signal-chief"
```

---

## 4. 报告产出与归档 (Reports Output)

每次圆桌分析运行成功后，系统会自动在根目录下的 `./output/<日期>/` 文件夹中输出以下内容：
1. **分析师独立报告**：各专家的独立分析过程文档，命名格式为 `<主题>-<专家头衔>.md`（如 `600150-估值分析师.md`）。
2. **圆桌共识研报**：由主理人汇总提炼的 `<主题>-圆桌报告.md`。
3. **高保真 HTML 可视化研报**：`<主题>-圆桌报告.html`（内嵌了各分析师的专属头像与精美的排版样式，完全独立，双击即可在浏览器中完美查看，适于转发分享）。
