# decision_engine/format_outputs.py
"""
OUTPUT FORMATTER.
Transforms internal data into rich, formatted DataFrames matching the UI design.
Generates:
1. Dashboard (Merged view of Holdings + Health + Actions)
2. Portfolio State (With P&L and Cost Basis)
3. Signals (With visual indicators)
UPDATED: Robust handling for Empty Portfolio (Cold Start).
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any
from utils.logger import setup_logger

log = setup_logger()


def format_all_sheets(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the creation of all display-ready DataFrames.
    """
    log.info("=== FORMATTING OUTPUTS (RICH VIEW) ===", tags=["DECISION", "FORMAT"])
   
    # Extract inputs
    analysis = universal_data.get('analysis', {})
    exec_plan = universal_data.get('execution_plan', {})
    state = universal_data.get('portfolio_state', {})
   
    # 1. ENRICHED PORTFOLIO STATE
    portfolio_df = _format_portfolio_state(state.get('holdings', pd.DataFrame()))
    universal_data['report_sheets']['portfolio_state'] = portfolio_df
   
    # 2. RICH SIGNALS
    signals_df = _format_signals(analysis.get('health_matrix_df', pd.DataFrame()))
    universal_data['report_sheets']['signals'] = signals_df
   
    # 3. WEEKLY ACTIONS
    actions_df = exec_plan.get('weekly_actions_df', pd.DataFrame())
    universal_data['report_sheets']['weekly_actions'] = actions_df
   
    # 4. MASTER DASHBOARD
    # This is the complex one: Merges State, Signals, and Actions into one view
    dashboard_df = _create_master_dashboard(portfolio_df, signals_df, actions_df, universal_data)
    universal_data['report_sheets']['dashboard'] = dashboard_df
   
    # 5. LOGS & HARVEST
    harvest_df = analysis.get('harvest_triggers_df', pd.DataFrame())
    if not harvest_df.empty:
        harvest_df['Date'] = datetime.now().strftime('%Y-%m-%d')
        universal_data['report_sheets']['harvest_log'] = harvest_df
    else:
        universal_data['report_sheets']['harvest_log'] = pd.DataFrame()
       
    universal_data['report_sheets']['logs'] = pd.DataFrame([
        {'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
         'Level': 'SUCCESS',
         'Module': 'Pipeline',
         'Message': f"Run Complete. Budget: {analysis.get('weekly_budget', 0):.2f}"}
    ])
   
    log.info("Outputs formatted successfully.", tags=["DECISION", "FORMAT", "SUCCESS"])
    return universal_data


def _format_portfolio_state(holdings: pd.DataFrame) -> pd.DataFrame:
    """Adds financial metrics: Cost Basis, Unrealized P&L, P&L %."""
    if holdings.empty: return pd.DataFrame()
   
    df = holdings.copy()
   
    # Ensure numeric
    cols = ['Units', 'Avg_Buy_Price', 'Current_Price']
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        else:
            df[c] = 0.0
       
    # Calculations
    df['Market_Value'] = df['Units'] * df['Current_Price']
    df['Cost_Basis'] = df['Units'] * df['Avg_Buy_Price']
    df['Unrealized_P&L'] = df['Market_Value'] - df['Cost_Basis']
   
    # Avoid division by zero
    df['P&L_%'] = df.apply(lambda x: (x['Unrealized_P&L'] / x['Cost_Basis'] * 100) if x['Cost_Basis'] > 0 else 0.0, axis=1)
   
    return df


def _format_signals(health_df: pd.DataFrame) -> pd.DataFrame:
    """Cleans up health matrix columns."""
    if health_df.empty: return pd.DataFrame()
   
    df = health_df.copy()
    df['Week_Date'] = datetime.now().strftime('%Y-%m-%d')
   
    # Select and Rename columns
    display_map = {
        'ETF': 'Ticker',
        'RSI': 'RSI_14',
        'Pass': 'Health_Status'
    }
    df.rename(columns=display_map, inplace=True)
    return df


def _create_master_dashboard(portfolio: pd.DataFrame, signals: pd.DataFrame, actions: pd.DataFrame, universal_data: Dict) -> pd.DataFrame:
    """
    Creates the 'Table 1' view.
    Joins all data sources into a single summary table.
    Robust to missing/empty data sources.
    """
    # Base: ETF Lineup from config to ensure we show everything
    lineup = universal_data['configs']['etf_lineup'].copy()
    if lineup.empty: return pd.DataFrame()
   
    # 1. Start with Ticker and Targets
    # Handle variation in column names from Excel
    target_col = next((c for c in lineup.columns if 'Target' in c), 'Target_%')
    dash = lineup[['Ticker', target_col]].copy()
    dash.rename(columns={target_col: 'Target Weight %'}, inplace=True)
   
    # 2. Merge Portfolio Info (Current Weight, Gap, Status)
    if not portfolio.empty:
        # Handle column variations
        curr_col = next((c for c in portfolio.columns if 'Current' in c and '%' in c), 'Current_%')
        gap_col = next((c for c in portfolio.columns if 'Gap' in c), 'Gap_%')
       
        port_mini = portfolio[['Ticker', curr_col, gap_col, 'Status', 'Current_Price']].copy()
        port_mini.rename(columns={
            curr_col: 'Current Weight %',
            gap_col: 'Gap',
            'Current_Price': 'Last Close'
        }, inplace=True)
        dash = pd.merge(dash, port_mini, on='Ticker', how='left')
   
    # 3. Merge Signals (Health Score)
    if not signals.empty:
        sig_mini = signals[['Ticker', 'Health_Score']].copy()
        dash = pd.merge(dash, sig_mini, on='Ticker', how='left')
       
    # 4. Merge Actions (Action This Week)
    if not actions.empty:
        actions['Action_String'] = actions.apply(_format_action_string, axis=1)
        act_mini = actions[['ETF', 'Action_String']].rename(columns={'ETF': 'Ticker', 'Action_String': 'Action This Week'})
        dash = pd.merge(dash, act_mini, on='Ticker', how='left')
   
    # 5. Ensure Columns Exist (FIX FOR COLD START)
    # If portfolio was empty, these columns won't exist after merge
    required_cols = ['Current Weight %', 'Gap', 'Status', 'Last Close', 'Health_Score', 'Action This Week']
    for col in required_cols:
        if col not in dash.columns:
            dash[col] = np.nan
    # 6. Fill NaNs
    dash['Current Weight %'] = dash['Current Weight %'].fillna(0)
    dash['Gap'] = dash['Gap'].fillna(0)
    dash['Status'] = dash['Status'].fillna('NONE')
    dash['Health_Score'] = dash['Health_Score'].fillna(0).astype(int)
    dash['Last Close'] = dash['Last Close'].fillna(0)
    dash['Action This Week'] = dash['Action This Week'].fillna('No Action')
   
    # 7. Add Derived Signal Column
    dash['Signal'] = dash['Health_Score'].apply(lambda x: 'BUY' if x == 4 else ('HOLD' if x == 3 else 'SKIP'))
   
    # Final Column Ordering
    cols = [
        'Ticker', 'Current Weight %', 'Target Weight %', 'Gap', 'Status',
        'Health_Score', 'Signal', 'Last Close', 'Action This Week'
    ]
    # Only keep cols that exist
    final_cols = [c for c in cols if c in dash.columns]
   
    return dash[final_cols]


def _format_action_string(row):
    """Formats action into readable string: 'Buy ₹X @ ₹Y' or 'Trim X units'."""
    action = row['Action']
    if action == 'BUY':
        return f"Buy ₹{row['Value']:.0f} @ ₹{row['Price']:.2f}"
    elif action == 'TRIM':
        return f"Trim {row['Units']} units ({row['Reason']})"
    return "No Action"