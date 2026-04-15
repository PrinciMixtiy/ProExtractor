"""
Configuration management for the Pro Extractor desktop application.

This module provides centralized configuration management with default values,
environment variable support, and JSON persistence.
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration with persistence and environment overrides."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Custom configuration directory path
        """
        self.config_dir = Path(config_dir or self._get_default_config_dir())
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._config = self._load_config()
    
    def _get_default_config_dir(self) -> str:
        """Get default configuration directory based on platform."""
        if os.name == 'nt':  # Windows
            return os.path.expandvars("%APPDATA%/pro-extractor")
        else:  # macOS/Linux
            home = Path.home()
            return str(home / ".config" / "pro-extractor")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create with defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    logger.debug(f"Configuration loaded from {self.config_file}")
                    return config_data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file {self.config_file}: {e}")
            except IOError as e:
                logger.error(f"Failed to read config file {self.config_file}: {e}")
        
        # Return default configuration
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "general": {
                "default_download_folder": str(Path.home() / "Downloads"),
                "default_filename_pattern": "{title}",
                "theme": "auto",  # auto, light, dark
                "language": "en"
            },
            "downloads": {
                "max_concurrent": 4,
                "retries_on_failure": 5,
                "retry_delay": 1000,
                "auto_resume": True,
                "default_quality": "720p",
                "default_format": "mp4",
                "embed_thumbnails": True,
                "auto_generate_subtitles": False,
                "subtitle_language": "en",
                "audio_only": False,
                "timeout": 30
            },
            "paths": {
                "data_dir": "",
                "log_dir": ""
            },
            "auth": {
                "browser_source": None,
                "default_cookies": False,
                "domain_overrides": {
                    "youtube.com": False,
                    "tiktok.com": False,
                    "instagram.com": False,
                    "facebook.com": False,
                    "twitter.com": False,
                    "x.com": False,
                    "twitch.tv": False,
                    "reddit.com": False
                }
            },
            "advanced": {
                "ffmpeg_path": "",
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'general.default_download_folder')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            # Check environment variable override
            env_key = f"PRO_EXTRACTOR_{key.upper().replace('.', '_')}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                return self._convert_env_value(env_value)
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'general.default_download_folder')
            value: Value to set
        """
        keys = key.split('.')
        current_config = self._config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current_config:
                current_config[k] = {}
            current_config = current_config[k]
        
        # Set the value
        current_config[keys[-1]] = value
        self.save()
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, default=str)
            logger.debug(f"Configuration saved to {self.config_file}")
        except IOError as e:
            logger.error(f"Failed to save config to {self.config_file}: {e}")
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = self._get_default_config()
        logger.info("Configuration reset to defaults")
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return self._config.copy()
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Handle boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value


# Global configuration instance
config = ConfigManager()
