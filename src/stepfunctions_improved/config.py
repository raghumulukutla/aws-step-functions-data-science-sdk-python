# Copyright 2024 Improved Step Functions Framework

"""
Configuration management using Dynaconf
"""

from dynaconf import Dynaconf
import os
from pathlib import Path

def setup_config(
    settings_files: list = None,
    environments: bool = True,
    envvar_prefix: str = "STEPFUNCTIONS",
    load_dotenv: bool = True
) -> Dynaconf:
    """
    Setup Dynaconf configuration for Step Functions
    
    Args:
        settings_files: List of configuration files to load
        environments: Whether to enable environment-specific configuration
        envvar_prefix: Prefix for environment variables
        load_dotenv: Whether to load .env files
    
    Returns:
        Configured Dynaconf instance
    """
    if settings_files is None:
        settings_files = ['settings.toml', '.secrets.toml']
    
    # Look for config files in current directory and config/ subdirectory
    config_paths = []
    for settings_file in settings_files:
        # Current directory
        if Path(settings_file).exists():
            config_paths.append(settings_file)
        # config/ subdirectory
        config_file = Path("config") / settings_file
        if config_file.exists():
            config_paths.append(str(config_file))
    
    return Dynaconf(
        envvar_prefix=envvar_prefix,
        settings_files=config_paths,
        environments=environments,
        load_dotenv=load_dotenv,
        merge_enabled=True,
        validators=[
            # Add validation rules
        ]
    )

# Default configuration instance
settings = setup_config()