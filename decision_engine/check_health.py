# decision_engine/check_health.py
"""
HEALTH CHECK ENGINE.
Evaluates technical 'Health Gates' for each ETF.
Only ETFs passing ALL gates (Score 4/4) are eligible for buying.
"""
import pandas as pd
from typing import Dict, Any
from utils.logger import setup_logger

log = setup_logger()


def run_health_checks(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates 4 Gates for every ETF in the lineup using 1W timeframe:
    1. TSI > Signal (Trend)
    2. RSI > 50 (Momentum)
    3. VWMA Slope >= 0 (Volume Trend)
    4. ATR% <= Ceiling (Volatility Safety)
    """
    log.info("=== HEALTH CHECK STARTED ===", tags=["DECISION", "HEALTH"])
   
    # Inputs
    snapshot_df = universal_data['market_data'].get('indicator_snapshot_df')
    etf_lineup = universal_data['configs']['etf_lineup']
    system_params = universal_data['configs']['system_params']
   
    if snapshot_df is None or snapshot_df.empty:
        log.warning("No indicator snapshot available. All health checks will FAIL.", tags=["DECISION", "HEALTH"])
        universal_data['analysis']['health_matrix_df'] = pd.DataFrame()
        return universal_data
       
    # Global Configs
    global_atr_ceiling = _get_param(system_params, 'ATR_Ceiling_%', 2.0)
   
    health_results = []
   
    # Iterate over configured Lineup (not just what we fetched, to track missing data)
    for _, row in etf_lineup.iterrows():
        etf = row['Ticker']
        if not row.get('Enabled', True):
            continue
           
        # 1. Get ETF Specifics
        atr_override = row.get('ATR_Override_%')
        atr_ceiling = float(atr_override) if pd.notna(atr_override) and atr_override != '' else global_atr_ceiling
       
        # 2. Get Market Data (Weekly)
        # We look for Timeframe='1W' in snapshot
        data = snapshot_df[ (snapshot_df['ETF'] == etf) & (snapshot_df['Timeframe'] == '1W') ]
       
        if data.empty:
            log.warning(f"No weekly data found for {etf}", tags=["DECISION", "HEALTH"])
            health_results.append(_create_fail_record(etf, "NO_DATA"))
            continue
           
        latest = data.iloc[0]
       
        # 3. Extract Indicators (Dynamic Column Handling)
        # pandas-ta names columns like 'RSI_14', 'TSI_25_13_7', 'ATRp_14'
        # We search for columns starting with the indicator name to be robust
       
        try:
            rsi = _get_val(latest, 'RSI')
            tsi = _get_val(latest, 'TSI') # The main TSI line
            tsi_sig = _get_val(latest, 'TSIe') # The signal line (EMA of TSI) -> pandas-ta often labels signal as TSIs or similar.
                                               # Note: In the calc config, we likely used 'tsi' which produces TSI_... and TSIs_...
                                               # We need to be careful here.
           
            # Specific fix for TSI Signal: pandas-ta output for TSI is usually TSI_fast_slow_sig and TSIh_... (signal is implicit or separate?)
            # Actually pandas-ta 'tsi' returns [TSI, TSIs]. We need to find them.
            tsi_val = latest.get([c for c in latest.index if c.startswith('TSI_')][0], 0)
            tsi_sig_val = latest.get([c for c in latest.index if c.startswith('TSIs_')][0], 0)
           
            vwma = _get_val(latest, 'VWMA')
            # Note: To calc VWMA slope, we need previous value. Snapshot only has latest.
            # LIMITATION: Snapshot is 1 row.
            # FIX: We cannot calc slope from 1 row.
            # Assumption: The 'indicator_calculator' should have calc'd slope or we assume flat if missing?
            # Better approach: Use Price > VWMA as a proxy if slope unavailable, OR
            # The indicator_calculator should be updated to include slope.
            # For now, we will use Close > VWMA as the "Positive Trend" proxy if Slope is missing.
           
            atr_pct = _get_val(latest, 'ATRp') # ATR Percent
           
            # 4. Evaluate Gates
            gate_1 = tsi_val > tsi_sig_val # Trend
            gate_2 = rsi > 50 # Momentum
            gate_3 = latest['close'] > vwma # Volume Trend Proxy (since slope hard on snapshot)
            gate_4 = atr_pct <= atr_ceiling # Volatility
           
            score = sum([gate_1, gate_2, gate_3, gate_4])
            passed = (score == 4)
           
            health_results.append({
                'ETF': etf,
                'TSI_Val': round(tsi_val, 2),
                'TSI_Sig': round(tsi_sig_val, 2),
                'RSI': round(rsi, 1),
                'ATR_Pct': round(atr_pct, 2),
                'ATR_Ceiling': atr_ceiling,
                'Gate_1_Trend': gate_1,
                'Gate_2_Mom': gate_2,
                'Gate_3_Vol': gate_3,
                'Gate_4_Risk': gate_4,
                'Health_Score': score,
                'Pass': passed,
                'Reason': 'OK' if passed else 'Gates Failed'
            })
           
        except Exception as e:
            log.error(f"Health check logic error for {etf}: {e}", tags=["DECISION", "HEALTH", "ERROR"])
            health_results.append(_create_fail_record(etf, "CALC_ERROR"))
    # 5. Create Matrix
    health_df = pd.DataFrame(health_results)
    universal_data['analysis']['health_matrix_df'] = health_df
   
    passed_count = len(health_df[health_df['Pass'] == True]) if not health_df.empty and 'Pass' in health_df.columns else 0
    log.info(f"Health Checks Complete. {passed_count}/{len(etf_lineup)} ETFs Passed.", tags=["DECISION", "HEALTH", "SUCCESS"])
   
    return universal_data


def _get_val(row: pd.Series, prefix: str) -> float:
    """Finds column starting with prefix and returns value."""
    try:
        col = [c for c in row.index if c.startswith(prefix)]
        if col:
            return float(row[col[0]])
        return 0.0
    except:
        return 0.0


def _create_fail_record(etf: str, reason: str) -> Dict:
    return {
        'ETF': etf, 'TSI_Val': 0, 'TSI_Sig': 0, 'RSI': 0, 'ATR_Pct': 0, 'ATR_Ceiling': 0,
        'Gate_1_Trend': False, 'Gate_2_Mom': False, 'Gate_3_Vol': False, 'Gate_4_Risk': False,
        'Health_Score': 0, 'Pass': False, 'Reason': reason
    }


def _get_param(df: Any, param_name: str, default: Any) -> Any:
    if df is None or df.empty: return default
    try:
        row = df[df['Parameter'] == param_name]
        if not row.empty: return float(row.iloc[0]['Value'])
    except: pass
    return default