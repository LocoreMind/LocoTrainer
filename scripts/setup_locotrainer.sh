#!/bin/bash
set -e

echo "=========================================="
echo "LocoTrainer-4B + vLLM 一键部署脚本"
echo "=========================================="

# 检查 Python 版本
PYTHON_CMD=$(command -v python3.11 || command -v python3.10 || command -v python3)
if [ -z "$PYTHON_CMD" ]; then
    echo "错误: 未找到 Python 3.10+，请先安装"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | awk '{print $2}')
echo "✓ 使用 Python $PYTHON_VERSION"

# 创建 venv
VENV_PATH="$HOME/.venv/locotrainer"
if [ -d "$VENV_PATH" ]; then
    echo "✓ 虚拟环境已存在: $VENV_PATH"
else
    echo "→ 创建虚拟环境: $VENV_PATH"
    $PYTHON_CMD -m venv "$VENV_PATH"
fi

# 激活环境
source "$VENV_PATH/bin/activate"

# 升级 pip
echo "→ 升级 pip"
pip install -U pip -q

# 安装 vLLM
echo "→ 安装 vLLM (需要几分钟)"
pip install vllm>=0.6.0 -q

# 安装 LocoTrainer
echo "→ 安装 LocoTrainer"
pip install locotrainer -q

# 验证安装
echo ""
echo "=========================================="
echo "安装验证"
echo "=========================================="
python -c "import vllm; print(f'✓ vLLM {vllm.__version__}')"
locotrainer --version | sed 's/^/✓ /'

# 创建启动脚本
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
echo "✓ 创建启动脚本: $START_SCRIPT"

# 创建 .env 模板
ENV_FILE="$HOME/.locotrainer.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'ENV_EOF'
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
    echo "✓ 创建配置文件: $ENV_FILE"
else
    echo "✓ 配置文件已存在: $ENV_FILE"
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 启动 vLLM 服务（后台运行）："
echo "   nohup $START_SCRIPT > ~/vllm.log 2>&1 &"
echo ""
echo "2. 或使用 screen（推荐）："
echo "   screen -S vllm"
echo "   $START_SCRIPT"
echo "   # Ctrl+A D 退出，服务继续运行"
echo ""
echo "3. 加载配置并运行 LocoTrainer："
echo "   source ~/.venv/locotrainer/bin/activate"
echo "   export \$(cat ~/.locotrainer.env | xargs)"
echo "   locotrainer run -q \"What are the default LoRA settings in ms-swift?\""
echo ""
echo "4. 查看日志："
echo "   tail -f ~/vllm.log"
echo ""
