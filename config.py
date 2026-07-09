import os
import sys
from dotenv import load_dotenv

# Load .env file
project_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(project_root, ".env"))

# Core configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Paths setup
NODE_PATH = os.getenv("NODE_PATH", "node")
SKILLS_DIR = os.path.join(project_root, "skills")
AGENTS_DIR = os.path.join(project_root, "agents")
AVATARS_DIR = os.path.join(project_root, "avatars")
TEMPLATES_DIR = os.path.join(project_root, "templates")

WESTOCK_DATA_SCRIPT = os.path.join(SKILLS_DIR, "westock-data", "scripts", "index.js")
WESTOCK_TOOL_SCRIPT = os.path.join(SKILLS_DIR, "westock-tool", "scripts", "index.js")
RENDER_HTML_SCRIPT = os.path.join(SKILLS_DIR, "md-to-html", "scripts", "render.py")

# Validate paths
def check_paths():
    missing = []
    for path_name, path_val in [
        ("westock-data script", WESTOCK_DATA_SCRIPT),
        ("westock-tool script", WESTOCK_TOOL_SCRIPT),
        ("agents directory", AGENTS_DIR)
    ]:
        if not os.path.exists(path_val):
            missing.append(f"{path_name} (path: {path_val})")
    if missing:
        print(f"Warning: The following paths are missing:\n" + "\n".join(missing), file=sys.stderr)

check_paths()
