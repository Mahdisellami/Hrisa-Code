"""Configuration management for Hrisa Code."""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """LLM model configuration."""

    name: str = "codellama"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=0)


class OllamaServerConfig(BaseModel):
    """Ollama server configuration."""

    host: str = "http://localhost:11434"
    timeout: int = 300


class ToolsConfig(BaseModel):
    """Tools configuration."""

    enable_file_operations: bool = True
    enable_command_execution: bool = True
    enable_search: bool = True
    command_timeout: int = 30
    max_file_size_mb: int = 10


class Config(BaseModel):
    """Main configuration for Hrisa Code."""

    model: ModelConfig = Field(default_factory=ModelConfig)
    ollama: OllamaServerConfig = Field(default_factory=OllamaServerConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    system_prompt: Optional[str] = None

    @classmethod
    def load(cls, config_path: Path) -> "Config":
        """Load configuration from a YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Loaded configuration
        """
        if not config_path.exists():
            return cls()

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data) if data else cls()

    def save(self, config_path: Path) -> None:
        """Save configuration to a YAML file.

        Args:
            config_path: Path to save the configuration
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)

    @classmethod
    def get_default_config_path(cls) -> Path:
        """Get the default configuration path.

        Returns:
            Default config path in user's home directory
        """
        return Path.home() / ".config" / "hrisa-code" / "config.yaml"

    @classmethod
    def get_project_config_path(cls, project_dir: Path) -> Path:
        """Get the project-specific configuration path.

        Args:
            project_dir: Project directory

        Returns:
            Project config path
        """
        return project_dir / ".hrisa" / "config.yaml"

    @classmethod
    def load_with_fallback(cls, project_dir: Optional[Path] = None) -> "Config":
        """Load configuration with fallback chain.

        Tries in order:
        1. Project-specific config (.hrisa/config.yaml)
        2. User config (~/.config/hrisa-code/config.yaml)
        3. Default config

        Args:
            project_dir: Optional project directory

        Returns:
            Loaded configuration
        """
        # Try project config
        if project_dir:
            project_config = cls.get_project_config_path(project_dir)
            if project_config.exists():
                return cls.load(project_config)

        # Try user config
        user_config = cls.get_default_config_path()
        if user_config.exists():
            return cls.load(user_config)

        # Return default
        return cls()
