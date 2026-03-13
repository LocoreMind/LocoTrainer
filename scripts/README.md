# Setup Scripts

This directory contains setup scripts for different LocoTrainer deployment scenarios.

## Available Scripts

### 1. `setup_locotrainer.sh` - CLI Only (Recommended for most users)

Installs LocoTrainer CLI with uv for use with external API providers.

**Use case**: You want to use LocoTrainer with OpenAI, DashScope, OpenRouter, or other cloud APIs.

**Requirements**: Python 3.10+

**Installation**:
```bash
curl -O https://raw.githubusercontent.com/LocoreMind/LocoTrainer/main/scripts/setup_locotrainer.sh
chmod +x setup_locotrainer.sh
./setup_locotrainer.sh
```

**What it does**:
- Checks/installs uv
- Creates venv at `~/.venv/locotrainer`
- Installs locotrainer via `uv pip install`
- Creates config template at `~/.locotrainer.env`

**After installation**:
```bash
# Edit config with your API key
nano ~/.locotrainer.env

# Run
source ~/.venv/locotrainer/bin/activate
export $(cat ~/.locotrainer.env | xargs)
locotrainer run -q "What are the default LoRA settings in ms-swift?"
```

---

### 2. `setup_locotrainer_vllm.sh` - vLLM + LocoTrainer-4B (For GPU users)

Installs vLLM + LocoTrainer for local deployment of LocoTrainer-4B model.

**Use case**: You have an NVIDIA GPU (40GB+ VRAM) and want to run LocoTrainer-4B locally at zero API cost.

**Requirements**:
- Python 3.10+
- NVIDIA GPU with 40GB+ VRAM (A100 40GB recommended for 128K context)
- CUDA 12.1+

**Installation**:
```bash
curl -O https://raw.githubusercontent.com/LocoreMind/LocoTrainer/main/scripts/setup_locotrainer_vllm.sh
chmod +x setup_locotrainer_vllm.sh
./setup_locotrainer_vllm.sh
```

**What it does**:
- Checks for NVIDIA GPU
- Checks/installs uv
- Creates venv at `~/.venv/locotrainer`
- Installs vLLM + locotrainer
- Creates `~/start_vllm.sh` startup script
- Creates config at `~/.locotrainer.env` (points to localhost:8080)

**After installation**:
```bash
# Start vLLM server (background)
nohup ~/start_vllm.sh > ~/vllm.log 2>&1 &

# Or use screen (recommended)
screen -S vllm
~/start_vllm.sh
# Press Ctrl+A D to detach

# Wait for model to load (check logs)
tail -f ~/vllm.log

# Run LocoTrainer
source ~/.venv/locotrainer/bin/activate
export $(cat ~/.locotrainer.env | xargs)
locotrainer run -q "How does ms-swift implement GRPO training?"
```

---

### 3. `setup_locotrainer_dev.sh` - Development Environment

Sets up development environment from source for contributors.

**Use case**: You want to contribute to LocoTrainer or modify the source code.

**Requirements**: Python 3.10+

**Installation**:
```bash
git clone https://github.com/LocoreMind/LocoTrainer.git
cd LocoTrainer
./scripts/setup_locotrainer_dev.sh
```

**What it does**:
- Checks/installs uv
- Runs `uv sync` to install dependencies
- Creates `.env` from `.env.example`

**After installation**:
```bash
# Edit config
nano .env

# Run from source
uv run locotrainer run -q "Your question"
```

---

## Quick Comparison

| Script | Install Location | Use Case | GPU Required |
|--------|-----------------|----------|--------------|
| `setup_locotrainer.sh` | `~/.venv/locotrainer` | Cloud API users | No |
| `setup_locotrainer_vllm.sh` | `~/.venv/locotrainer` | Local model deployment | Yes (40GB+) |
| `setup_locotrainer_dev.sh` | `./LocoTrainer/.venv` | Development/contribution | No |

---

## Troubleshooting

**Script fails with "uv: command not found"**
- The script should auto-install uv, but if it fails, manually install:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
  ```

**vLLM script fails with CUDA errors**
- Verify CUDA version: `nvidia-smi`
- vLLM requires CUDA 12.1+
- Check GPU memory: `nvidia-smi --query-gpu=memory.total --format=csv`

**"locotrainer: command not found" after installation**
- Activate the venv first: `source ~/.venv/locotrainer/bin/activate`
- Or use full path: `~/.venv/locotrainer/bin/locotrainer`
