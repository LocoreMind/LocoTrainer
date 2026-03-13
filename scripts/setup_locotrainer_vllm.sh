#!/bin/bash
set -e

echo "=========================================="
echo "LocoTrainer + vLLM Setup"
echo "=========================================="
echo ""

# Check GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "Warning: nvidia-smi not found. This script requires NVIDIA GPU."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

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
echo "→ Installing vLLM (this may take several minutes)..."
uv pip install vllm -q
echo "→ Installing locotrainer..."
uv pip install locotrainer -q
echo "→ Upgrading transformers to 5.2.0 (required for LocoTrainer-4B)..."
uv pip install transformers==5.2.0 -q

# Verify
echo ""
echo "=========================================="
echo "Installation Complete"
echo "=========================================="
python -c "import vllm; print(f'✓ vLLM {vllm.__version__}')"
locotrainer --version | sed 's/^/✓ /'

# Create vLLM startup script
START_SCRIPT="$HOME/start_vllm.sh"
cat > "$START_SCRIPT" << 'SCRIPT_EOF'
#!/bin/bash
source ~/.venv/locotrainer/bin/activate
python -m vllm.entrypoints.openai.api_server \
    --model LocoreMind/LocoTrainer-4B \
    --dtype bfloat16 \
    --max-model-len 131072 \
    --gpu-memory-utilization 0.90 \
    --max-num-seqs 8 \
    --host 0.0.0.0 \
    --port 8080 \
    --served-model-name LocoTrainer-4B
SCRIPT_EOF
chmod +x "$START_SCRIPT"
echo "✓ Created vLLM startup script: $START_SCRIPT"

# Create config for local vLLM
ENV_FILE="$HOME/.locotrainer.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'ENV_EOF'
# LocoTrainer Configuration (local vLLM)
LOCOTRAINER_API_KEY=local
LOCOTRAINER_BASE_URL=http://localhost:8080/v1
LOCOTRAINER_MODEL=LocoTrainer-4B
LOCOTRAINER_MAX_TURNS=20
LOCOTRAINER_MAX_TOKENS=8192
LOCOTRAINER_TEMPERATURE=0.7
LOCOTRAINER_TOP_P=0.9
LOCOTRAINER_FREQUENCY_PENALTY=0.0
LOCOTRAINER_PRESENCE_PENALTY=0.0
ENV_EOF
    echo "✓ Created config file: $ENV_FILE"
else
    echo "✓ Config file exists: $ENV_FILE"
fi

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Start vLLM server (background):"
echo "   nohup $START_SCRIPT > ~/vllm.log 2>&1 &"
echo ""
echo "2. Or use screen (recommended):"
echo "   screen -S vllm"
echo "   $START_SCRIPT"
echo "   # Press Ctrl+A D to detach"
echo ""
echo "3. Wait for model to load (check logs):"
echo "   tail -f ~/vllm.log"
echo ""
echo "4. Run LocoTrainer:"
echo "   source ~/.venv/locotrainer/bin/activate"
echo "   export \$(cat ~/.locotrainer.env | xargs)"
echo "   locotrainer run -q \"What are the default LoRA settings in ms-swift?\""
echo ""
echo "Hardware requirements:"
echo "  - NVIDIA GPU with 40GB+ VRAM (A100 40GB recommended)"
echo "  - CUDA 12.1+"
echo ""
