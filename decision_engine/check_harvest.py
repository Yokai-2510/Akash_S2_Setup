# decision_engine/check_harvest.py
"""
HARVEST TRIGGER ENGINE.
Checks for profit-taking opportunities (H1, H2, H3 triggers).
Applies Safety Floors (DriftBand, CoreFloor) and Sleeve Caps.
"""
import pandas as pd
from typing import Dict, Any, Tuple
from utils.logger import setup_logger

log = setup_logger()


def find_harvest_triggers(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Logic:
    1. Filter holdings in profit (Avg Price < Current Price).
    2. Check Triggers:
       - H1 Stretch: RSI > 70
       - H2 Vol Spike: ATR% > 80th Percentile (Using fixed threshold 3.5% as proxy if history missing)
       - H3 Breakdown: TSI Cross Down
    3. Calculate Trim Size (10-15%)
    4. Apply Floors: Ensure trim doesn't push weight below (Target - Drift) or (CoreFloor * Target).
    """
    log.info("=== HARVEST CHECK STARTED ===", tags=["DECISION", "HARVEST"])
   
    # Inputs
    holdings = universal_data['portfolio_state']['holdings']
    snapshot = universal_data['market_data'].get('indicator_snapshot_df')
    system_params = universal_data['configs']['system_params']
   
    if holdings.empty:
        log.info("Portfolio is empty. No harvest needed.", tags=["DECISION", "HARVEST"])
        universal_data['analysis']['harvest_triggers_df'] = pd.DataFrame()
        return universal_data
    # Configs
    drift_band = _get_param(system_params, 'DriftBand_%', 10.0)
    core_floor_pct = _get_param(system_params, 'CoreFloor_%', 70.0)
    max_trim_pct = _get_param(system_params, 'MaxTrimPerETF_%', 25.0)
   
    harvest_actions = []
   
    for _, pos in holdings.iterrows():
        etf = pos['Ticker']
        units = float(pos['Units'])
        avg_price = float(pos['Avg_Buy_Price'])
        curr_price = float(pos['Current_Price'])
       
        # 1. Check Profitability (Only harvest Green)
        if curr_price <= avg_price:
            continue
           
        if snapshot is None or snapshot.empty:
            continue
           
        # Get Technical Data
        data = snapshot[ (snapshot['ETF'] == etf) & (snapshot['Timeframe'] == '1W') ]
        if data.empty: continue
       
        latest = data.iloc[0]
       
        # 2. Check Triggers
        trigger_type, base_trim = _check_trigger_conditions(latest)
       
        if not trigger_type:
            continue
           
        # 3. Calculate Proposed Trim
        # Limit base trim by MaxTrimPerETF
        actual_trim_pct = min(base_trim, max_trim_pct)
       
        # 4. Apply Floors
        # Current Weight vs Target Weight Logic
        # We need safe metrics. If 'Current_%' is missing, calculate it?
        # Assuming 'Current_%' exists from State Reader.
        curr_weight = float(pos.get('Current_%', 0))
        target_weight = float(pos.get('Target_%', 0))
       
        # Floor 1: Drift Floor (Target - Drift)
        drift_floor = target_weight - drift_band
       
        # Floor 2: Core Floor (Target * CoreFloor%)
        core_floor = target_weight * (core_floor_pct / 100.0)
       
        # The absolute floor is the max of these two (highest safety level)
        hard_floor_weight = max(drift_floor, core_floor)
       
        # Calculate Post-Trim Weight
        # Weight to shed = curr_weight * (actual_trim_pct / 100)
        post_trim_weight = curr_weight * (1 - (actual_trim_pct/100.0))
       
        if post_trim_weight < hard_floor_weight:
            # Trim is too aggressive, hitting floor.
            # Adjust trim to land exactly on floor
            allowed_shed = max(0, curr_weight - hard_floor_weight)
            if allowed_shed == 0:
                log.info(f"Skipping harvest for {etf}: Hit Floor (Weight {curr_weight}% vs Floor {hard_floor_weight}%)", tags=["DECISION", "HARVEST", "FLOOR"])
                continue
           
            # Recalculate trim %
            actual_trim_pct = (allowed_shed / curr_weight) * 100.0
       
        # 5. Final Units
        trim_units = int(units * (actual_trim_pct / 100.0))
       
        if trim_units > 0:
            harvest_actions.append({
                'ETF': etf,
                'Trigger': trigger_type,
                'Trim_Units': trim_units,
                'Trim_Pct': round(actual_trim_pct, 2),
                'Est_Value': round(trim_units * curr_price, 2)
            })
            log.info(f"Harvest Triggered: {etf} ({trigger_type}) -> Trim {trim_units} units", tags=["DECISION", "HARVEST"])
    # 6. Save
    df = pd.DataFrame(harvest_actions)
    universal_data['analysis']['harvest_triggers_df'] = df
   
    return universal_data


def _check_trigger_conditions(row: pd.Series) -> Tuple[str, float]:
    """
    Returns (TriggerName, TrimPercent).
    Returns (None, 0.0) if no trigger.
    """
    # Parse Indicators
    try:
        rsi = _get_val(row, 'RSI')
        atr_pct = _get_val(row, 'ATRp')
        tsi_val = _get_val(row, 'TSI_')
        tsi_sig = _get_val(row, 'TSIs_')
    except:
        return None, 0.0
   
    # H1: Stretch
    if rsi > 70:
        return "H1_Stretch", 10.0
       
    # H2: Volatility Spike
    # Ideally check percentile. Proxy: ATR > 3.5% (High vol for ETF)
    if atr_pct > 3.5:
        return "H2_VolSpike", 15.0
       
    # H3: Breakdown
    # TSI Crossed Down (Val < Sig) AND was previously up?
    # Snapshot limitation: We only see current state.
    # If TSI < Sig, it's in a downtrend. We use this as a "stay clean" trigger if also Profit protected.
    if tsi_val < tsi_sig:
        return "H3_Breakdown", 15.0
       
    return None, 0.0


def _get_val(row: pd.Series, prefix: str) -> float:
    col = [c for c in row.index if c.startswith(prefix)]
    if col: return float(row[col[0]])
    return 0.0


def _get_param(df: Any, param_name: str, default: Any) -> Any:
    if df is None or df.empty: return default
    try:
        row = df[df['Parameter'] == param_name]
        if not row.empty: return float(row.iloc[0]['Value'])
    except: pass
    return default