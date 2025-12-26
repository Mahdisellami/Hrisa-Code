"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import yaml

from hrisa_code.core.config import Config, ModelConfig, OllamaServerConfig, ToolsConfig


def test_model_config_defaults():
    """Test ModelConfig default values."""
    config = ModelConfig()
    assert config.name == "qwen2.5:72b"
    assert config.temperature == 0.7
    assert config.top_p == 0.9
    assert config.top_k == 40


def test_ollama_server_config_defaults():
    """Test OllamaServerConfig default values."""
    config = OllamaServerConfig()
    assert config.host == "http://localhost:11434"
    assert config.timeout == 300


def test_tools_config_defaults():
    """Test ToolsConfig default values."""
    config = ToolsConfig()
    assert config.enable_file_operations is True
    assert config.enable_command_execution is True
    assert config.enable_search is True


def test_config_defaults():
    """Test Config default values."""
    config = Config()
    assert isinstance(config.model, ModelConfig)
    assert isinstance(config.ollama, OllamaServerConfig)
    assert isinstance(config.tools, ToolsConfig)
    assert config.system_prompt is None


def test_config_save_and_load():
    """Test saving and loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        # Create and save config
        original_config = Config(
            model=ModelConfig(name="mistral", temperature=0.5)
        )
        original_config.save(config_path)

        # Load config
        loaded_config = Config.load(config_path)

        assert loaded_config.model.name == "mistral"
        assert loaded_config.model.temperature == 0.5


def test_config_load_nonexistent():
    """Test loading non-existent config returns defaults."""
    config = Config.load(Path("/nonexistent/config.yaml"))
    assert config.model.name == "qwen2.5:72b"


def test_get_default_config_path():
    """Test getting default config path."""
    path = Config.get_default_config_path()
    assert path == Path.home() / ".config" / "hrisa-code" / "config.yaml"


def test_get_project_config_path():
    """Test getting project config path."""
    project_dir = Path("/tmp/project")
    path = Config.get_project_config_path(project_dir)
    assert path == project_dir / ".hrisa" / "config.yaml"
