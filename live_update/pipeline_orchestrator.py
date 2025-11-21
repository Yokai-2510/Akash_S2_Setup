# live_update/pipeline_orchestrator.py

"""
PIPELINE ORCHESTRATOR.
Decides which phases to run based on changes.
"""

from typing import Dict, Any
from utils.logger import setup_logger

# Import Phase Modules
from data_pipeline.upstox_auth import process_authentication
from data_pipeline.instrument_fetcher import sync_instrument_master
from data_pipeline.ohlcv_downloader import process_ohlcv_sync
from data_pipeline.indicator_calculator import process_indicator_calculation
from decision_engine.calculate_budget import calculate_weekly_budget
from decision_engine.check_health import run_health_checks
from decision_engine.check_harvest import find_harvest_triggers
from decision_engine.generate_actions import generate_weekly_actions
from decision_engine.format_outputs import format_all_sheets
from connectors.sheets_writer import write_all_sheets_to_excel

log = setup_logger()

def execute_smart_pipeline(universal_data: Dict[str, Any], changes: Dict[str, bool]) -> Dict[str, Any]:
    """
    Runs selective phases based on change flags.
    """
    log.info("=== ORCHESTRATING SMART RUN ===", tags=["ORCHESTRATOR"])
    
    # Logic: 
    # If Lineup changed -> Need new Data.
    # If Config/Portfolio changed -> Only need Recalc (Decisions).
    run_data = changes['lineup_changed'] or changes['force_refresh']
    run_decisions = True # Always run if triggered
    
    # --- PHASE 2 ---
    if run_data:
        log.info("Phase 2: Market Data Refresh Required.", tags=["ORCHESTRATOR"])
        universal_data = process_authentication(universal_data)
        universal_data = sync_instrument_master(universal_data)
        universal_data = process_ohlcv_sync(universal_data)
        universal_data = process_indicator_calculation(universal_data)
    else:
        log.info("Phase 2: Skipped (Data valid). Checking in-memory snapshot...", tags=["ORCHESTRATOR"])
        # Failsafe: If snapshot missing in memory, calc it
        if universal_data['market_data']['indicator_snapshot_df'].empty:
             universal_data = process_indicator_calculation(universal_data)

    # --- PHASE 3 ---
    if run_decisions:
        log.info("Phase 3: Strategy Execution.", tags=["ORCHESTRATOR"])
        universal_data = calculate_weekly_budget(universal_data)
        universal_data = run_health_checks(universal_data)
        universal_data = find_harvest_triggers(universal_data)
        universal_data = generate_weekly_actions(universal_data)
        universal_data = format_all_sheets(universal_data)
    
    # --- PHASE 4 ---
    log.info("Phase 4: Writing Output.", tags=["ORCHESTRATOR"])
    universal_data = write_all_sheets_to_excel(universal_data)
    
    return universal_data