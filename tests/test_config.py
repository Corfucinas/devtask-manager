"""Tests for config module."""
import os, tempfile, pytest
from unittest.mock import patch
from src.config import load_config, save_config

class TestLoadConfig:
    def test_defaults(self):
        with patch("src.config.get_config_path", return_value="/nonexistent/config.json"):
            config = load_config()
            assert config["default_priority"] == "medium"
            assert config["color_output"] is True

class TestSaveConfig:
    def test_save_and_load(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with patch("src.config.get_config_path", return_value=path):
            save_config({"default_priority": "high", "color_output": False})
            config = load_config()
            assert config["default_priority"] == "high"
            assert config["color_output"] is False
        os.remove(path)
