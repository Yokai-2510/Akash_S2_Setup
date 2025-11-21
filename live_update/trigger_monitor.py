# live_update/trigger_monitor.py

"""
TRIGGER MONITOR.
Polls the Excel file periodically to check if 'UPDATE_TRIGGER' is TRUE.
"""

from typing import Dict, Any
from connectors.sheets_reader import load_config_and_portfolio
from utils.logger import setup_logger

log = setup_logger()

def monitor_excel_trigger(universal_data: Dict[str, Any]) -> bool:
    """
    Reloads config/portfolio to check for trigger flag.
    Returns True if trigger detected.
    """
    try:
        # We reload data here to check the flag
        universal_data = load_config_and_portfolio(universal_data)
        
        is_triggered = universal_data['change_detection'].get('update_trigger', False)
        
        if is_triggered:
            log.info(">> UPDATE TRIGGER DETECTED <<", tags=["MONITOR"])
            return True
            
        return False
        
    except Exception as e:
        # Don't crash on file read errors (e.g., file open by user), just wait
        log.warning(f"Monitor polling suppressed: {e}", tags=["MONITOR"])
        return False