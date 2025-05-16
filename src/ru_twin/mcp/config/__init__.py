from typing import Dict, Any, Optional
from pydantic import BaseModel

class ConfigSchema(BaseModel):
    """Base configuration schema"""
    name: str
    version: str
    description: Optional[str] = None
    settings: Dict[str, Any] = {}

class Config:
    """Configuration manager class"""
    
    def __init__(self):
        self._config: Dict[str, Any] = {
            "name": "RU Twin MCP",
            "version": "1.0.0",
            "description": "Mission Control Platform Configuration",
            "settings": {}
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self._config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration with dictionary"""
        self._config.update(config_dict)
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self._config

# Create global config instance
config = Config()

__all__ = ['Config', 'ConfigSchema', 'config']
