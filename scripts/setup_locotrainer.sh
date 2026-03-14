#!/bin/bash
set -e

echo "=========================================="
echo "LocoTrainer Setup (CLI only)"
echo "=========================================="
echo ""

# Check Python version
PYTHON_CMD=$(command -v python3.11 || command -v python3.10 || command -v python3)
if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.10+ not found. Please install Python first."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | awk '{print $2}')
echo "✓ Using Python $PYTHON_VERSION"

# Check/install uv
if ! command -v uv &> /dev/null; then
    echo "→ Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✓ uv already installed"
fi

# Create venv
VENV_PATH="$HOME/.venv/locotrainer"
if [ -d "$VENV_PATH" ]; then
    echo "✓ Virtual environment exists: $VENV_PATH"
else
    echo "→ Creating virtual environment: $VENV_PATH"
    uv venv "$VENV_PATH" --python "$PYTHON_CMD"
fi

# Activate and install
source "$VENV_PATH/bin/activate"
echo "→ Installing locotrainer..."
uv pip install locotrainer -q

# Verify
echo ""
echo "=========================================="
echo "Installation Complete"
echo "=========================================="
locotrainer --version | sed 's/^/✓ /'

# Create config template
ENV_FILE="$HOME/.locotrainer.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'ENV_EOF'
# LocoTrainer Configuration
# Edit these values for your API provider

LOCOTRAINER_API_KEY=your-api-key-here
LOCOTRAINER_BASE_URL=https://api.openai.com/v1
LOCOTRAINER_MODEL=gpt-4o
LOCOTRAINER_MAX_TURNS=20
LOCOTRAINER_MAX_TOKENS=8192
LOCOTRAINER_TEMPERATURE=0.7
LOCOTRAINER_TOP_P=0.9
LOCOTRAINER_FREQUENCY_PENALTY=0.0
LOCOTRAINER_PRESENCE_PENALTY=0.0
ENV_EOF
    echo "✓ Created config template: $ENV_FILE"
else
    echo "✓ Config file exists: $ENV_FILE"
fi

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Edit your API configuration:"
echo "   nano ~/.locotrainer.env"
echo ""
echo "2. Load config and run:"
echo "   source ~/.venv/locotrainer/bin/activate"
echo "   export \$(cat ~/.locotrainer.env | xargs)"
echo "   locotrainer run -q \"What are the default LoRA settings in ms-swift?\""
echo ""
echo "Supported API providers:"
echo "  - OpenAI: https://api.openai.com/v1"
echo "  - DashScope: https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
echo "  - OpenRouter: https://openrouter.ai/api/v1"
echo "  - MiniMax: https://api.minimax.io/v1"
echo ""
