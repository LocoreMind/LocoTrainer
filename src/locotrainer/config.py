"""Configuration — loads from .env, environment variables, or CLI overrides."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    # API settings (OpenAI-compatible)
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"

    # Agent settings
    thinking_budget: int = 8192
    max_tokens: int = 8192
    max_turns: int = 20

    # Sampling parameters
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Paths
    codebase: str = "."
    output_dir: str = "./output"

    # Extra model kwargs (enable_thinking, etc.)
    extra_body: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls, env_file: str | None = None) -> "Config":
        """Load config from .env file and environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        cfg = cls()
        cfg.api_key = os.getenv("LOCOTRAINER_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        cfg.base_url = os.getenv("LOCOTRAINER_BASE_URL", os.getenv("OPENAI_BASE_URL", cfg.base_url))
        cfg.model = os.getenv("LOCOTRAINER_MODEL", cfg.model)
        cfg.thinking_budget = int(os.getenv("LOCOTRAINER_THINKING_BUDGET", str(cfg.thinking_budget)))
        cfg.max_tokens = int(os.getenv("LOCOTRAINER_MAX_TOKENS", str(cfg.max_tokens)))
        cfg.max_turns = int(os.getenv("LOCOTRAINER_MAX_TURNS", str(cfg.max_turns)))
        cfg.temperature = float(os.getenv("LOCOTRAINER_TEMPERATURE", str(cfg.temperature)))
        cfg.top_p = float(os.getenv("LOCOTRAINER_TOP_P", str(cfg.top_p)))
        cfg.frequency_penalty = float(os.getenv("LOCOTRAINER_FREQUENCY_PENALTY", str(cfg.frequency_penalty)))
        cfg.presence_penalty = float(os.getenv("LOCOTRAINER_PRESENCE_PENALTY", str(cfg.presence_penalty)))
        cfg.codebase = os.getenv("LOCOTRAINER_CODEBASE", cfg.codebase)
        cfg.output_dir = os.getenv("LOCOTRAINER_OUTPUT_DIR", cfg.output_dir)

        # Enable thinking if budget > 0 (for Qwen, DeepSeek, etc.)
        enable = os.getenv("LOCOTRAINER_ENABLE_THINKING", "")
        if enable.lower() in ("1", "true", "yes"):
            cfg.extra_body = {
                "enable_thinking": True,
                "thinking_budget": cfg.thinking_budget,
            }

        return cfg
