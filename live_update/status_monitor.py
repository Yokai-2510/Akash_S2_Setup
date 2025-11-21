# live_update/status_manager.py

"""
STATUS MANAGER.
Updates the SYSTEM_CONTROL sheet in Excel to reflect pipeline state.
"""

from typing import Dict, Any
from datetime import datetime
from connectors.sheets_writer import update_control_cells
from utils.logger import setup_logger

log = setup_logger()

def set_status_running(universal_data: Dict[str, Any]):
    """Marks the system as RUNNING in Excel."""
    update_control_cells(universal_data, {
        'RUN_STATUS': 'RUNNING',
        'ERROR_MESSAGE': ''
    })

def set_status_success(universal_data: Dict[str, Any]):
    """Marks run as SUCCESS, resets Trigger, updates Timestamp."""
    update_control_cells(universal_data, {
        'UPDATE_TRIGGER': 'FALSE',
        'RUN_STATUS': 'SUCCESS',
        'LAST_RUN_DATE': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ERROR_MESSAGE': ''
    })

def set_status_error(universal_data: Dict[str, Any], error_msg: str):
    """Marks run as ERROR and logs the message in Excel."""
    safe_msg = str(error_msg)[:250] # Truncate to avoid Excel limits
    
    update_control_cells(universal_data, {
        'UPDATE_TRIGGER': 'FALSE',
        'RUN_STATUS': 'ERROR',
        'ERROR_MESSAGE': safe_msg
    })