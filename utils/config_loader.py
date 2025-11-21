"""
Centralized configuration loader for system and strategy configs.
Loads JSON files, validates structure, and returns parsed configurations.
UPDATED: Loads from 'source/' directory and validates 'data_urls'.
"""

import json
import os
from typing import Dict, Any, Tuple
from utils.logger import setup_logger

log = setup_logger()


def load_all_configs(project_root: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load and validate both system and strategy configuration files."""
    
    log.info("Loading configuration files from 'source' directory...", tags=["CONFIG", "LOAD"])
    
    system_config_path = os.path.join(project_root, 'source', 'system_config.json')
    strategy_config_path = os.path.join(project_root, 'source', 'strategy_config.json')
    
    system_config = _load_json_file(system_config_path, "System Config")
    strategy_config = _load_json_file(strategy_config_path, "Strategy Config")
    
    _validate_system_config(system_config)
    _validate_strategy_config(strategy_config)
    
    log.info("Configuration files loaded successfully", tags=["CONFIG", "SUCCESS"])
    
    return system_config, strategy_config


def _load_json_file(file_path: str, config_name: str) -> Dict[str, Any]:
    """Load and parse a single JSON configuration file."""
    
    if not os.path.exists(file_path):
        log.critical(f"{config_name} file not found: {file_path}", tags=["CONFIG", "ERROR"])
        raise FileNotFoundError(f"{config_name} file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        log.info(f"Loaded {config_name}", tags=["CONFIG"])
        return config
        
    except json.JSONDecodeError as e:
        log.critical(f"Invalid JSON in {config_name}: {e}", tags=["CONFIG", "ERROR"])
        raise ValueError(f"Invalid JSON in {config_name}: {e}")


def _validate_system_config(config: Dict[str, Any]) -> None:
    """Validate system config has all required sections."""
    
    # UPDATED: Changed 'data_sources' to 'data_urls' to match system_config.json
    required_sections = [
        'system', 'debug_controls', 'data_urls', 
        'data_acquisition', 'cache_policies', 'paths', 'google_sheets'
    ]
    
    missing = [section for section in required_sections if section not in config]
    
    if missing:
        raise ValueError(f"System config missing sections: {missing}")
    
    # Validate critical paths exist
    required_paths = ['credentials_file', 'token_cache_file', 'ohlcv_data_dir']
    missing_paths = [p for p in required_paths if p not in config['paths']]
    
    if missing_paths:
        raise ValueError(f"System config missing path keys: {missing_paths}")
    
    # Warn if Google Sheets ID not configured (only if not in local mode)
    if config['system'].get('data_source_mode') != 'local_excel':
        if not config['google_sheets'].get('spreadsheet_id'):
            log.warning("Google Sheets spreadsheet_id not configured", tags=["CONFIG", "WARNING"])


def _validate_strategy_config(config: Dict[str, Any]) -> None:
    """Validate strategy config has all required sections."""
    
    required_sections = [
        'universe', 'indicators', 'allocation_rules', 
        'risk_controls', 'health_gates', 'harvest_triggers'
    ]
    
    missing = [section for section in required_sections if section not in config]
    
    if missing:
        raise ValueError(f"Strategy config missing sections: {missing}")
    
    # Validate ETF list not empty
    if not config['universe'].get('etfs_to_track'):
        raise ValueError("etfs_to_track cannot be empty")
    
    # Validate timeframes specified
    if not config['universe'].get('timeframes'):
        raise ValueError("timeframes cannot be empty")