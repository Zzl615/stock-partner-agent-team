#!/bin/bash
set -e

echo "============================================="
echo "Initializing Stock-Partner Agent-Team Project"
echo "============================================="

# Navigate to project root
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 1. Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[*] Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "[*] Virtual environment (.venv) already exists."
fi

# 2. Activate Virtual Environment and Install dependencies
echo "[*] Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create .env file if it does not exist
if [ ! -f ".env" ]; then
    echo "[*] Creating .env file from .env.example..."
    cp .env.example .env
    echo "    -> Please open .env and add your GEMINI_API_KEY or OPENAI_API_KEY!"
else
    echo "[*] .env file already exists."
fi

# 4. Check Node.js installation
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node -v)
    echo "[✓] Node.js is installed ($NODE_VERSION)."
else
    echo "[Warning] Node.js is not found. Please install Node.js >= 18 to run quantitative skills."
fi

echo "============================================="
echo "[✓] Setup completed successfully!"
echo "To activate environment:  source .venv/bin/activate"
echo "To run the team:          python main.py --help"
echo "============================================="
