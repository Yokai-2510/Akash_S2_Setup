# main.py

"""
S2 TRADING SYSTEM - CENTRAL ORCHESTRATOR.
Flow: Run Phases 1-4 (Startup) -> Enter Phase 5 Loop (if Daemon).
"""

import sys
import os
import time
import argparse

# --- PHASE 1: INIT ---
from utils.initialize_data import initialize_universal_data
from connectors.sheets_reader import load_config_and_portfolio
from utils.logger import setup_logger

# --- PHASE 2: MARKET DATA ---
from data_pipeline.upstox_auth import process_authentication
from data_pipeline.instrument_fetcher import sync_instrument_master
from data_pipeline.ohlcv_downloader import process_ohlcv_sync
from data_pipeline.indicator_calculator import process_indicator_calculation

# --- PHASE 3: DECISION ENGINE ---
from decision_engine.calculate_budget import calculate_weekly_budget
from decision_engine.check_health import run_health_checks
from decision_engine.check_harvest import find_harvest_triggers
from decision_engine.generate_actions import generate_weekly_actions
from decision_engine.format_outputs import format_all_sheets

# --- PHASE 4: OUTPUT ---
from connectors.sheets_writer import write_all_sheets_to_excel

# --- PHASE 5: LIVE UPDATE ---
from live_update.trigger_monitor import monitor_excel_trigger
from live_update.change_detector import detect_changes
from live_update.pipeline_orchestrator import execute_smart_pipeline
from live_update.status_monitor import set_status_running, set_status_success, set_status_error

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='single_run', choices=['single_run', 'daemon'])
    args = parser.parse_args()

    log = setup_logger()
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    try:
        log.info(f"=== S2 SYSTEM STARTUP ({args.mode.upper()}) ===", tags=["SYSTEM"])

        # ---------------------------------------------------------
        # LINEAR STARTUP (Runs once to initialize state & data)
        # ---------------------------------------------------------
        
        # Phase 1: Load Config & State
        universal_data = initialize_universal_data(project_root)
        universal_data = load_config_and_portfolio(universal_data)

        # Phase 2: Market Data
        universal_data = process_authentication(universal_data)
        universal_data = sync_instrument_master(universal_data)
        universal_data = process_ohlcv_sync(universal_data)
        universal_data = process_indicator_calculation(universal_data)

        # Phase 3: Strategy
        universal_data = calculate_weekly_budget(universal_data)
        universal_data = run_health_checks(universal_data)
        universal_data = find_harvest_triggers(universal_data)
        universal_data = generate_weekly_actions(universal_data)
        universal_data = format_all_sheets(universal_data)

        # Phase 4: Write Initial Result
        universal_data = write_all_sheets_to_excel(universal_data)
        log.info("=== INITIALIZATION & FIRST RUN COMPLETE ===", tags=["SYSTEM"])

        # ---------------------------------------------------------
        # PHASE 5: DAEMON MODE (Loop)
        # ---------------------------------------------------------
        if args.mode == 'daemon':
            log.info("Entering Live Monitoring Loop...", tags=["DAEMON"])
            poll_time = universal_data['configs']['system_settings']['google_sheets'].get('poll_interval_seconds', 10)
            
            while True:
                try:
                    # 1. Poll for Trigger
                    if monitor_excel_trigger(universal_data):
                        log.info("Trigger detected. Starting update...", tags=["DAEMON"])
                        set_status_running(universal_data)
                        
                        # 2. Smart Execution
                        changes = detect_changes(universal_data)
                        universal_data = execute_smart_pipeline(universal_data, changes)
                        
                        # 3. Reset
                        set_status_success(universal_data)
                        log.info("Update complete. Waiting for trigger...", tags=["DAEMON"])
                    
                    time.sleep(poll_time)
                    
                except KeyboardInterrupt:
                    log.info("Daemon stopped by user.", tags=["SYSTEM"])
                    break
                except Exception as e:
                    log.error(f"Daemon loop error: {e}", tags=["DAEMON"])
                    set_status_error(universal_data, str(e))
                    time.sleep(poll_time)

    except Exception as e:
        log.critical(f"FATAL SYSTEM ERROR: {e}", tags=["SYSTEM", "CRITICAL"], exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()