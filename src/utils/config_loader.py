"""Configuration loader for YAML config files"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

_config_cache: Optional[Dict[str, Any]] = None


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default path.
    
    Returns:
        Dict containing configuration
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    if config_path is None:
        # Default config path
        base_dir = Path(__file__).parent.parent.parent
        config_path = base_dir / "config" / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        _config_cache = yaml.safe_load(f)
    
    return _config_cache


def get_config() -> Dict[str, Any]:
    """
    Get cached configuration or load if not cached.
    
    Returns:
        Dict containing configuration
    """
    if _config_cache is None:
        return load_config()
    return _config_cache
