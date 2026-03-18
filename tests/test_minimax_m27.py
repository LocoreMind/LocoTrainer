"""Tests for MiniMax M2.7 model configuration."""

import os
import unittest
from unittest.mock import patch

from locotrainer.config import PROVIDERS, Config


class TestMiniMaxProvider(unittest.TestCase):
    """Verify MiniMax provider preset includes M2.7 as default."""

    def test_minimax_preset_exists(self):
        self.assertIn("minimax", PROVIDERS)

    def test_minimax_default_model_is_m27(self):
        self.assertEqual(PROVIDERS["minimax"]["model"], "MiniMax-M2.7")

    def test_minimax_base_url(self):
        self.assertEqual(PROVIDERS["minimax"]["base_url"], "https://api.minimax.io/v1")

    def test_minimax_api_key_env(self):
        self.assertEqual(PROVIDERS["minimax"]["api_key_env"], "MINIMAX_API_KEY")

    @patch.dict(os.environ, {
        "LOCOTRAINER_PROVIDER": "minimax",
        "MINIMAX_API_KEY": "test-key-123",
    }, clear=False)
    def test_from_env_minimax_provider(self):
        """Config.from_env with LOCOTRAINER_PROVIDER=minimax uses M2.7."""
        cfg = Config.from_env()
        self.assertEqual(cfg.model, "MiniMax-M2.7")
        self.assertEqual(cfg.base_url, "https://api.minimax.io/v1")
        self.assertEqual(cfg.api_key, "test-key-123")

    @patch.dict(os.environ, {
        "LOCOTRAINER_PROVIDER": "minimax",
        "MINIMAX_API_KEY": "test-key",
        "LOCOTRAINER_MODEL": "MiniMax-M2.5",
    }, clear=False)
    def test_explicit_model_overrides_preset(self):
        """Explicit LOCOTRAINER_MODEL overrides the provider default."""
        cfg = Config.from_env()
        self.assertEqual(cfg.model, "MiniMax-M2.5")

    def test_old_models_still_usable(self):
        """Old models can be selected via explicit LOCOTRAINER_MODEL override."""
        with patch.dict(os.environ, {
            "LOCOTRAINER_PROVIDER": "minimax",
            "MINIMAX_API_KEY": "k",
            "LOCOTRAINER_MODEL": "MiniMax-M2.7-highspeed",
        }):
            cfg = Config.from_env()
            self.assertEqual(cfg.model, "MiniMax-M2.7-highspeed")


if __name__ == "__main__":
    unittest.main()
