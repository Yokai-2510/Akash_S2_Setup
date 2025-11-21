# decision_engine/calculate_budget.py
"""
BUDGET CALCULATOR.
Determines weekly capital allocation based on Gap-to-Target and Glide Path.
Uses Initial_Capital from config for calculations.
"""
from typing import Dict, Any
from utils.logger import setup_logger

log = setup_logger()


def calculate_weekly_budget(universal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates 'Weekly_S2_Capacity': The max INR amount available to deploy this week.
   
    Formula:
      Gap = (Target% - Current%) * Total_Capital
      Base_Budget = Gap / Weeks_to_Glide
      Capacity = Min(Base_Budget, Transfer_Cap, S2_Budget_Cap) + Carry_Forward
    """
    log.info("=== BUDGET CALCULATION STARTED ===", tags=["DECISION", "BUDGET"])
   
    # 1. Extract Context
    summary = universal_data['portfolio_state']['summary']
    params = universal_data['configs']['system_params']
   
    # Get Initial Capital from config (this is the total portfolio value)
    initial_capital = _get_param(params, 'Initial_Capital', 1000000)
    
    # Current S2 value and weight
    current_s2_value = summary.get('total_s2_value', 0.0)
    
    # If we have holdings, use actual weight. Otherwise calculate from initial capital
    if current_s2_value > 0 and initial_capital > 0:
        current_pct = (current_s2_value / initial_capital) * 100
    else:
        current_pct = 0.0
   
    # 2. Get Parameters (with defaults)
    target_pct = _get_param(params, 'S2_Target_%', 34.0)
    weeks_to_glide = _get_param(params, 'Weeks_to_Glide', 52)
    transfer_cap_pct = _get_param(params, 'Weekly_Transfer_Cap_%', 5.0)
    s2_budget_cap_pct = _get_param(params, 'S2_Weekly_Budget_Cap_%', 1.25)
   
    # 3. Calculate Gap using Initial Capital
    gap_pct = target_pct - current_pct
    gap_value = (gap_pct / 100.0) * initial_capital
   
    log.info(f"Capital: ₹{initial_capital:,.0f} | Target={target_pct}% | Current={current_pct:.2f}% | Gap={gap_pct:.2f}% (₹{gap_value:,.0f})",
             tags=["DECISION", "BUDGET"])
   
    # 4. Calculate Base Budget
    weekly_base_budget = 0.0
    if gap_value > 0 and weeks_to_glide > 0:
        weekly_base_budget = gap_value / weeks_to_glide
       
    # 5. Apply Caps based on Initial Capital
    cap_transfer_inr = (transfer_cap_pct / 100.0) * initial_capital
    cap_s2_budget_inr = (s2_budget_cap_pct / 100.0) * initial_capital
    effective_cap = min(cap_transfer_inr, cap_s2_budget_inr)
   
    final_budget = min(weekly_base_budget, effective_cap)
   
    # Store Analysis
    universal_data['analysis']['weekly_budget'] = max(0.0, final_budget)
    universal_data['analysis']['gap_to_target'] = gap_value
    universal_data['analysis']['accrued_carry'] = max(0.0, weekly_base_budget - final_budget)
    universal_data['analysis']['initial_capital'] = initial_capital
    
    log.info(f"Weekly Budget: ₹{final_budget:,.2f} (Cap: ₹{effective_cap:,.0f})", tags=["DECISION", "BUDGET", "SUCCESS"])
   
    return universal_data


def _get_param(df, param_name: str, default):
    """Helper to safely extract parameters from the dataframe."""
    if df is None:
        return default
    
    # Handle DataFrame
    if hasattr(df, 'empty'):
        if df.empty:
            return default
        try:
            row = df[df['Parameter'] == param_name]
            if not row.empty:
                val = row.iloc[0]['Value']
                try:
                    return float(val)
                except:
                    return val
        except:
            pass
    
    return default