# live_update/change_detector.py

"""
CHANGE DETECTOR.
Compares current Excel state with cached state to determine required pipeline phases.
"""

import json
import os
import pandas as pd
from typing import Dict, Any
from utils.logger import setup_logger

log = setup_logger()

def detect_changes(universal_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Compares current loaded data vs 'state_cache.json'.
    Returns dict of flags: config_changed, lineup_changed, portfolio_changed.
    """
    path_config = universal_data['configs']['system_settings']['paths']
    cache_path = os.path.join(universal_data['system']['project_root'], path_config['state_cache_file'])
    
    current_state = _capture_current_state(universal_data)
    
    changes = {
        'config_changed': False,
        'lineup_changed': False,
        'portfolio_changed': False,
        'force_refresh': False
    }
    
    if not os.path.exists(cache_path):
        log.info("No state cache found. Forcing full refresh.", tags=["DETECT"])
        changes['force_refresh'] = True
        _save_state_cache(cache_path, current_state)
        return changes

    try:
        with open(cache_path, 'r') as f:
            cached_state = json.load(f)
            
        if current_state['system_params'] != cached_state.get('system_params'):
            log.info("Detected change in System Parameters.", tags=["DETECT"])
            changes['config_changed'] = True
            
        if current_state['etf_lineup'] != cached_state.get('etf_lineup'):
            log.info("Detected change in ETF Lineup.", tags=["DETECT"])
            changes['lineup_changed'] = True
            
        if current_state['portfolio'] != cached_state.get('portfolio'):
            log.info("Detected change in Portfolio Holdings.", tags=["DETECT"])
            changes['portfolio_changed'] = True
            
    except Exception as e:
        log.warning(f"Change detection error: {e}. Forcing full refresh.", tags=["DETECT"])
        changes['force_refresh'] = True

    _save_state_cache(cache_path, current_state)
    return changes

def _capture_current_state(universal_data: Dict) -> Dict:
    def _hash_df(df):
        if df is None or df.empty: return "EMPTY"
        return str(pd.util.hash_pandas_object(df, index=True).sum())

    return {
        'system_params': _hash_df(universal_data['configs'].get('system_params')),
        'etf_lineup': _hash_df(universal_data['configs'].get('etf_lineup')),
        'portfolio': _hash_df(universal_data['portfolio_state'].get('holdings'))
    }

def _save_state_cache(path: str, state: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(state, f)