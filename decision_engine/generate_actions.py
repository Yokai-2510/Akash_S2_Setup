# decision_engine/generate_actions.py
"""
ACTION GENERATION ENGINE.
Combines Budget, Health, and Harvest data to produce final Weekly Actions.
Calculates GTT Entry prices.
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from utils.logger import setup_logger

log = setup_logger()


def generate_weekly_actions(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates 'weekly_actions_df':
    1. Priority: Process Trims (from Harvest)
    2. Priority: Process Buys (from Budget + Health)
    3. Apply Single-ETF Caps
    4. Calculate GTT Price (Friday Close - 0.5 * ATR)
    """
    log.info("=== GENERATING ACTIONS ===", tags=["DECISION", "ACTIONS"])
   
    # Inputs
    budget = universal_data['analysis'].get('weekly_budget', 0.0)
    health_df = universal_data['analysis'].get('health_matrix_df')
    harvest_df = universal_data['analysis'].get('harvest_triggers_df')
    holdings = universal_data['portfolio_state']['holdings']
    lineup = universal_data['configs']['etf_lineup']
    snapshot = universal_data['market_data']['indicator_snapshot_df']
    system_params = universal_data['configs']['system_params']
   
    actions = []
   
    # 1. PROCESS TRIMS
    if harvest_df is not None and not harvest_df.empty:
        for _, row in harvest_df.iterrows():
            etf = row['ETF']
            # Get current price from holdings or snapshot
            price = _get_price(etf, holdings, snapshot)
           
            actions.append({
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'ETF': etf,
                'Action': 'TRIM',
                'Units': int(row['Trim_Units']),
                'Price': price,
                'Value': float(row['Est_Value']),
                'Reason': row['Trigger']
            })
            
    # 2. PROCESS BUYS
    # Filter Eligibility: Health Score = 4 AND Underweight
    # Underweight Logic: Gap > 0? We generally buy things that have a Gap to Target.
   
    eligible_buys = []
   
    if health_df is not None and not health_df.empty:
        passing_etfs = health_df[health_df['Pass'] == True]['ETF'].tolist()
       
        for etf in passing_etfs:
            # Check Weight
            target = _get_target_weight(etf, lineup)
            current = _get_current_weight(etf, holdings)
           
            if current < target:
                # It is underweight and healthy
                eligible_buys.append(etf)
               
    # 3. ALLOCATE BUDGET
    # Strategy: Equal weight allocation to eligible ETFs (Simple & Robust)
    # Or Proportional to Gap? Let's do Proportional to Gap for better gliding.
   
    if eligible_buys and budget > 1000: # Min threshold
        # Calculate total gap points
        total_gap_points = 0
        gaps = {}
       
        for etf in eligible_buys:
            t = _get_target_weight(etf, lineup)
            c = _get_current_weight(etf, holdings)
            gap = max(0, t - c)
            gaps[etf] = gap
            total_gap_points += gap
           
        # Allocate
        for etf in eligible_buys:
            if total_gap_points == 0: break
           
            allocation_share = gaps[etf] / total_gap_points
            allocated_amount = budget * allocation_share
           
            # Get ATR for GTT
            atr_val, close_price = _get_atr_and_close(etf, snapshot)
            if close_price == 0: continue
           
            # GTT Entry: Close - 0.5 * ATR
            gtt_price = close_price - (0.5 * atr_val)
           
            # Units
            units = int(allocated_amount / gtt_price)
           
            if units > 0:
                actions.append({
                    'Date': datetime.now().strftime('%Y-%m-%d'),
                    'ETF': etf,
                    'Action': 'BUY',
                    'Units': units,
                    'Price': round(gtt_price, 2),
                    'Value': round(units * gtt_price, 2),
                    'Reason': 'Health_Pass_Underweight'
                })
    else:
        log.info("No eligible buys found or insufficient budget.", tags=["DECISION", "ACTIONS"])
    # 4. Save
    df = pd.DataFrame(actions)
    universal_data['execution_plan']['weekly_actions_df'] = df
   
    log.info(f"Actions Generated: {len(df)} orders.", tags=["DECISION", "ACTIONS", "SUCCESS"])
    return universal_data
# --- Helpers ---


def _get_price(etf: str, holdings: pd.DataFrame, snapshot: pd.DataFrame) -> float:
    # Try holdings first
    if not holdings.empty:
        row = holdings[holdings['Ticker'] == etf]
        if not row.empty:
            return float(row.iloc[0]['Current_Price'])
    # Try snapshot
    if not snapshot.empty:
        row = snapshot[ (snapshot['ETF'] == etf) & (snapshot['Timeframe'] == '1W') ]
        if not row.empty:
            return float(row.iloc[0]['close'])
    return 0.0


def _get_target_weight(etf: str, lineup: pd.DataFrame) -> float:
    if lineup.empty: return 0.0
    row = lineup[lineup['Ticker'] == etf]
    if not row.empty: return float(row.iloc[0]['Target_%'])
    return 0.0


def _get_current_weight(etf: str, holdings: pd.DataFrame) -> float:
    if holdings.empty: return 0.0
    row = holdings[holdings['Ticker'] == etf]
    if not row.empty: return float(row.iloc[0].get('Current_%', 0))
    return 0.0


def _get_atr_and_close(etf: str, snapshot: pd.DataFrame) -> tuple:
    if snapshot.empty: return 0.0, 0.0
    row = snapshot[ (snapshot['ETF'] == etf) & (snapshot['Timeframe'] == '1W') ]
    if row.empty: return 0.0, 0.0
   
    # Find ATR col
    atr_col = [c for c in row.columns if c.startswith('ATRr') or c.startswith('ATR_')] # pandas-ta raw ATR
    atr = float(row.iloc[0][atr_col[0]]) if atr_col else 0.0
    close = float(row.iloc[0]['close'])
    return atr, close