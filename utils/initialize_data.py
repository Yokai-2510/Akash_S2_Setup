"""
Universal Data Structure Initialization.
Creates central data container with all required sections and loads configurations.
"""

import os
from datetime import datetime
import pandas as pd
from typing import Dict, Any

from utils.logger import setup_logger
from utils.config_loader import load_all_configs
from utils.validators import (
    validate_system_config_values, 
    validate_strategy_config_values
)

log = setup_logger()


def initialize_universal_data(project_root: str) -> Dict[str, Any]:
    """
    Initialize empty universal_data structure and load all configurations.
    Creates the central data container that flows through the entire pipeline.
    """
    
    log.info("=== INITIALIZING UNIVERSAL DATA ===", tags=["INIT", "START"])
    
    # Load configuration files
    system_config, strategy_config = load_all_configs(project_root)
    
    # Validate configuration values
    system_errors = validate_system_config_values(system_config)
    strategy_errors = validate_strategy_config_values(strategy_config)
    
    if system_errors:
        log.error(f"System config validation errors: {system_errors}", tags=["INIT", "ERROR"])
        raise ValueError(f"System config invalid: {system_errors}")
    
    if strategy_errors:
        log.error(f"Strategy config validation errors: {strategy_errors}", tags=["INIT", "ERROR"])
        raise ValueError(f"Strategy config invalid: {strategy_errors}")
    
    # Create universal data structure
    universal_data = _create_data_structure(project_root, system_config, strategy_config)
    
    # Log initialization summary
    _log_initialization_summary(universal_data)
    
    log.info("=== INITIALIZATION COMPLETE ===", tags=["INIT", "END"])
    
    return universal_data


def _create_data_structure(
    project_root: str, 
    system_config: Dict[str, Any], 
    strategy_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Create the complete universal_data structure with all sections."""
    
    return {
        # System runtime context
        "system": {
            "project_root": project_root,
            "run_timestamp": datetime.now().isoformat(),
            "status": "INITIALIZING",
            "execution_mode": system_config['system']['execution_mode'],
            "debug_flags": system_config['debug_controls']
        },
        
        # All configurations
        "configs": {
            "system_settings": system_config,
            "strategy_settings": strategy_config,
            "system_params": pd.DataFrame(),  # Loaded from Excel
            "etf_lineup": pd.DataFrame(),     # Loaded from Excel
            "universe_settings": {
                "etfs_to_track": strategy_config['universe']['etfs_to_track'],
                "timeframes_to_calculate": strategy_config['universe']['timeframes']
            },
            "indicator_settings": strategy_config['indicators']['enabled_indicators']
        },
        
        # Portfolio state from Excel
        "portfolio_state": {
            "holdings": pd.DataFrame(),
            "summary": {}
        },
        
        # Market data from Phase 2
        "market_data": {
            "etf_master_list": pd.DataFrame(),
            "ohlcv_file_paths": {},
            "indicator_snapshot_df": pd.DataFrame(),
            "indicator_history_path": ""
        },
        
        # Analysis results from Phase 3
        "analysis": {
            "weekly_budget": 0.0,
            "gap_to_target": 0.0,
            "accrued_carry": 0.0,
            "health_matrix_df": pd.DataFrame(),
            "harvest_triggers_df": pd.DataFrame()
        },
        
        # Execution plan from Phase 3
        "execution_plan": {
            "weekly_actions_df": pd.DataFrame()
        },
        
        # Formatted output sheets
        "report_sheets": {
            "dashboard": pd.DataFrame(),
            "config": pd.DataFrame(),
            "portfolio_state": pd.DataFrame(),
            "signals": pd.DataFrame(),
            "weekly_actions": pd.DataFrame(),
            "harvest_log": pd.DataFrame(),
            "logs": pd.DataFrame()
        },
        
        # Change tracking for Phase 5
        "change_detection": {
            "update_trigger": False,
            "last_run_timestamp": "",
            "cached_state_hash": {},
            "changes_detected": {
                "config_changed": False,
                "etf_lineup_changed": False,
                "portfolio_changed": False,
                "force_full_refresh": False
            },
            "modules_to_rerun": []
        },
        
        # Authentication
        "access_token": "",
        "token_expiry": ""
    }


def _log_initialization_summary(universal_data: Dict[str, Any]) -> None:
    """Log key details about the initialized system."""
    
    system = universal_data['system']
    configs = universal_data['configs']
    
    log.info(f"Execution mode: {system['execution_mode']}", tags=["INIT"])
    log.info(f"Project root: {system['project_root']}", tags=["INIT"])
    
    # Log active debug flags
    active_flags = [k for k, v in system['debug_flags'].items() if v]
    if active_flags:
        log.info(f"Active debug flags: {', '.join(active_flags)}", tags=["INIT", "DEBUG"])
    
    # Log ETF universe
    etfs = configs['universe_settings']['etfs_to_track']
    timeframes = configs['universe_settings']['timeframes_to_calculate']
    log.info(f"Tracking {len(etfs)} ETFs across {len(timeframes)} timeframes", tags=["INIT"])