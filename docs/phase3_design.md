# Phase 3: Decision Engine - Design Plan & Modular Architecture

## 🎯 Overview

**Purpose**: Transform indicator data and portfolio state into actionable weekly trading decisions following the S2 strategy rules.

**Input**: 
- Indicator snapshot (18 rows: 6 ETFs × 3 timeframes)
- Current portfolio holdings
- Strategy configuration (targets, caps, health thresholds)

**Output**: 
- Weekly actions DataFrame (BUY/TRIM/NO_ACTION for each ETF)
- Analysis DataFrames (health checks, harvest triggers)
- Execution-ready GTT order specifications

---

## 📐 Module Structure

```
decision_engine/
├── 1_calculate_budget.py       # Budget allocation logic
├── 2_check_health.py            # Health gate evaluation
├── 3_check_harvest.py           # Profit-taking trigger detection
├── 4_generate_actions.py        # Final action plan generation
└── 5_format_outputs.py          # Prepare data for reporting
```

---

## 🧩 Module-by-Module Design

### **Module 1: `1_calculate_budget.py`**

**Function**: `calculate_weekly_budget(universal_data) -> universal_data`

#### Purpose
Calculate how much capital is available for deployment this week based on the Asset Allocator's target and glide path logic.

#### Key Logic

**Step 1: Extract Allocator Inputs**
```
- Current S2 weight (from portfolio summary)
- Target S2 weight (from CONFIG)
- Weeks_to_Glide (from CONFIG, default: 52)
```

**Step 2: Calculate Gap**
```
Gap_to_Target_S2 (₹) = (Target_S2_% - Current_S2_%) × Total_Capital
```

**Step 3: Apply Glide Formula**
```
Weekly_S2_Base_Budget (₹) = Gap_to_Target_S2 ÷ Weeks_to_Glide
```

**Step 4: Apply Safety Caps**
```
Weekly_S2_Capacity (₹) = min(
    Weekly_S2_Base_Budget,
    Weekly_Transfer_Cap_% × Total_Capital,
    S2_Weekly_Budget_Cap_% × Total_Capital
)
```

**Step 5: Handle Carry-Forward (Optional)**
```
IF Enable_Carry_Forward = TRUE:
    Accrued_S2_Carry += Unspent_from_Last_Week
    Weekly_S2_Capacity = min(caps, base_budget + accrued_carry)
```

#### Outputs to universal_data
```python
universal_data['analysis']['weekly_budget'] = Weekly_S2_Capacity (₹)
universal_data['analysis']['accrued_carry'] = Accrued_S2_Carry (₹)
universal_data['analysis']['gap_to_target'] = Gap_to_Target_S2 (₹)
```

#### Edge Cases
- **Gap is negative** (overweight): Budget = 0, flag for harvest checks only
- **Gap is zero** (at target): Budget = 0, monitor only
- **Weeks_to_Glide = 0**: Error, must be > 0

---

### **Module 2: `2_check_health.py`**

**Function**: `run_health_checks(universal_data) -> universal_data`

#### Purpose
Evaluate each ETF against health criteria to determine eligibility for new purchases this week.

#### Key Logic

**Step 1: Load Latest Indicators**
```
FOR each ETF in etfs_to_track:
    - Extract weekly (1W) timeframe indicators from snapshot
    - Get: TSI, TSI_Signal, RSI, VWMA_slope, ATR%
```

**Step 2: Apply Health Gates (Binary Pass/Fail)**
```
Gate 1: TSI > TSI_Signal ✓/✗
Gate 2: RSI > 50 ✓/✗
Gate 3: VWMA_slope ≥ 0 ✓/✗
Gate 4: ATR% ≤ ATR_Ceiling_% (check ETF-specific override) ✓/✗
```

**Step 3: Calculate Health Score**
```
Health_Score = Count of passed gates (0-4)
Pass = TRUE if Health_Score = 4, else FALSE
```

**Step 4: Build Health Matrix**
```
Columns:
- ETF
- TSI, TSI_Signal (values)
- RSI (value)
- VWMA_Slope (value)
- ATR% (value)
- ATR_Ceiling_% (threshold)
- Gate_1_Pass, Gate_2_Pass, Gate_3_Pass, Gate_4_Pass (booleans)
- Health_Score (0-4)
- Pass (boolean)
```

#### Outputs to universal_data
```python
universal_data['analysis']['health_matrix_df'] = health_df
# DataFrame with one row per ETF, all health checks and scores
```

#### Edge Cases
- **Missing indicator data**: Mark ETF as FAIL, log warning
- **ATR override not specified**: Use default 2.0%
- **All ETFs fail**: Valid outcome, carry budget forward

---

### **Module 3: `3_check_harvest.py`**

**Function**: `find_harvest_triggers(universal_data) -> universal_data`

#### Purpose
Identify ETFs that meet profit-taking criteria and calculate trim amounts.

#### Key Logic

**Step 1: Filter Eligible Positions**
```
FOR each holding in portfolio:
    IF Current_Price > Avg_Buy_Price:  # In profit
        Proceed to trigger checks
    ELSE:
        Skip (no trimming allowed on losses)
```

**Step 2: Check Harvest Triggers (Weekly Timeframe)**
```
H1 - Stretch:
    - RSI > 70, OR
    - Close > 13W_High by >1×ATR, OR
    - Distance from 20DMA > 2×ATR

H2 - Volatility Spike:
    - ATR% > 80th percentile (6-month rolling), OR
    - Week-to-week ATR% change > 35%

H3 - Health Breakdown:
    - TSI crosses below Signal, AND/OR
    - Close < 50DMA (first break)
```

**Step 3: Determine Trim Size**
```
IF H1 fires: Base_Trim = 10% of units
IF H2 fires: Base_Trim = 15% of units
IF H3 fires: Base_Trim = 15% (25% if BOTH TSI↓ AND <50DMA)

Apply per-ETF cap: Trim ≤ 25% of units
Apply sleeve cap: Total trims ≤ 12% of S2 value
```

**Step 4: Validate Against Floors**
```
Floor 1 (Drift): Post-trim weight ≥ (Target - DriftBand)
Floor 2 (Core): Post-trim weight ≥ CoreFloor% × Target

IF trim violates floor:
    Scale down trim to stay above floor
```

**Step 5: Apply Cooldown**
```
Check last 4 weeks:
    IF ETF already harvested 2 times:
        Skip this trim (cooldown active)
```

#### Outputs to universal_data
```python
universal_data['analysis']['harvest_triggers_df'] = harvest_df

Columns:
- ETF
- In_Profit (boolean)
- Trigger (H1/H2/H3 or None)
- Signal_Snapshot (RSI, TSI/Signal, 50DMA_status, ATR%)
- Base_Trim_% (10/15/25)
- Floor_Adjusted_Trim_% (after floors applied)
- Cap_Adjusted_Trim_% (after caps applied)
- Units_to_Trim (final)
- Trim_Value_₹ (units × current_price)
- Cooldown_Active (boolean)
- Action (TRIM or SKIP)
```

#### Edge Cases
- **Multiple triggers fire**: Use strongest trim % (max of H1/H2/H3)
- **Sleeve cap exceeded**: Scale all trims proportionally
- **Cooldown active**: Override trigger, set Action = SKIP

---

### **Module 4: `4_generate_actions.py`**

**Function**: `generate_weekly_actions(universal_data) -> universal_data`

#### Purpose
Combine budget, health, and harvest analysis into final actionable weekly plan.

#### Key Logic

**Step 1: Initialize Actions List**
```
weekly_actions = []
remaining_budget = weekly_budget_₹
```

**Step 2: Process Harvest Actions (Priority 1)**
```
FOR each ETF in harvest_triggers_df WHERE Action = TRIM:
    CREATE action:
        - ETF
        - Action = TRIM
        - Units = Units_to_Trim
        - Price = Current_Price
        - Amount_₹ = Units × Price
        - Reason = Trigger (H1/H2/H3)
        - Pre_% = Current weight
        - Post_% = Weight after trim
    
    ADD to weekly_actions
```

**Step 3: Process Buy Actions (Priority 2)**
```
Filter ETFs:
    - Pass = TRUE (from health matrix)
    - Current_% < Target_% (underweight)
    - NOT on cooldown

Sort by priority:
    - Tie-breaker 1: Lower ATR% (less volatile)
    - Tie-breaker 2: Higher RSI (stronger momentum)

FOR each eligible ETF in sorted order:
    IF remaining_budget ≤ 0:
        BREAK
    
    Calculate slice size:
        IF Health_Score = 4:
            Slice = Full (use proportional allocation)
        IF Health_Score = 3:
            Slice = Half (0.5× proportional allocation)
    
    Calculate amount:
        Proportional_Share = (Target_% - Current_%) / Total_Gap_% × Weekly_Budget
        Adjusted_Amount = Proportional_Share × Slice_Multiplier
    
    Apply caps:
        - Single_ETF_Max_% of S2
        - Tag/Sector caps (e.g., Financials ≤25%)
        - Remaining_Budget
    
    Calculate GTT entry:
        GTT_Price = Friday_Close - (0.5 × ATR)
        Units = floor(Adjusted_Amount / GTT_Price)
    
    IF Units > 0:
        CREATE action:
            - ETF
            - Action = BUY
            - Units
            - Price = GTT_Price
            - Amount_₹ = Units × GTT_Price
            - Reason = "UNDER+H4" or "UNDER+H3"
            - Pre_% = Current weight
            - Post_% = Weight after buy
        
        ADD to weekly_actions
        Deduct from remaining_budget
```

**Step 4: Handle No-Action ETFs**
```
FOR each tracked ETF NOT in weekly_actions:
    CREATE action:
        - ETF
        - Action = NO_ACTION
        - Reason = NEAR / OVER / FAIL_HEALTH / COOLDOWN
```

**Step 5: Update Carry-Forward**
```
IF Enable_Carry_Forward = TRUE:
    Unspent = remaining_budget
    Accrued_S2_Carry += Unspent
```

#### Outputs to universal_data
```python
universal_data['execution_plan']['weekly_actions_df'] = actions_df

Columns:
- Week_Date (Monday of current week)
- ETF_ID
- ETF (Ticker)
- Action (BUY/TRIM/NO_ACTION)
- Units
- Price (GTT or Current)
- Amount_₹
- Reason (UNDER+H4, H1_Stretch, etc.)
- Pre_% (weight before)
- Post_% (weight after)
- Trigger (for trims: H1/H2/H3, else "-")
- Status (PLANNED - to be executed)
```

#### Edge Cases
- **No budget + no trims**: All ETFs → NO_ACTION
- **All ETFs fail health**: Carry budget forward
- **Caps conflict**: Prioritize earlier ETFs in sorted list, skip later ones

---

### **Module 5: `5_format_outputs.py`**

**Function**: `format_all_sheets(universal_data) -> universal_data`

#### Purpose
Transform analysis and execution data into final DataFrames ready for Google Sheets writing (Phase 4).

#### Key Logic

**Sheet 1: DASHBOARD (Summary View)**
```
Columns:
- Metric, Value, Change_from_Last_Week

Rows:
- Total S2 Value (₹)
- Current S2 Weight (%)
- Target S2 Weight (%)
- Gap to Target (₹)
- Weekly Budget (₹)
- Accrued Carry (₹)
- ETFs Passing Health (count)
- Actions This Week (BUY/TRIM counts)
- Orders Pending (count)
```

**Sheet 2: CONFIG (Echo Configuration)**
```
Same structure as input CONFIG sheet
(This is already loaded, just pass through)
```

**Sheet 3: PORTFOLIO_STATE (Updated Holdings)**
```
Columns:
- ETF_ID
- Ticker
- Units (projected after actions)
- Avg_Cost (recalculated)
- Current_Price
- Market_Value
- Current_%
- Target_%
- Gap_%
- Status (UNDER/NEAR/OVER)
```

**Sheet 4: SIGNALS (Technical Indicators)**
```
Columns:
- Week_Date
- ETF_ID
- ETF
- TSI, TSI_Signal
- RSI
- VWMA_Slope
- ATR%
- vs_50DMA
- vs_13W_High
- Health_Score
- Pass
```

**Sheet 5: WEEKLY_ACTIONS (Execution Log)**
```
Direct copy of weekly_actions_df from Module 4
```

**Sheet 6: HARVEST_LOG (Profit-Taking History)**
```
Append-only log of all harvest actions
Columns: Same as harvest_triggers_df + Execution_Date
```

**Sheet 7: LOGS (System Events)**
```
Columns:
- Timestamp
- Module
- Level (INFO/WARNING/ERROR)
- Message
- Tags
```

#### Outputs to universal_data
```python
universal_data['report_sheets']['dashboard'] = dashboard_df
universal_data['report_sheets']['config'] = config_df
universal_data['report_sheets']['portfolio_state'] = updated_portfolio_df
universal_data['report_sheets']['signals'] = signals_df
universal_data['report_sheets']['weekly_actions'] = actions_df
universal_data['report_sheets']['harvest_log'] = harvest_log_df
universal_data['report_sheets']['logs'] = logs_df
```

---

## 🔗 Data Flow Diagram

```
INPUT: universal_data
    ├── configs (from Phase 1)
    ├── portfolio_state (from Phase 1)
    └── market_data.indicator_snapshot_df (from Phase 2)

MODULE 1: calculate_budget
    → analysis.weekly_budget
    → analysis.gap_to_target
    → analysis.accrued_carry

MODULE 2: check_health
    → analysis.health_matrix_df

MODULE 3: check_harvest
    → analysis.harvest_triggers_df

MODULE 4: generate_actions
    → execution_plan.weekly_actions_df

MODULE 5: format_outputs
    → report_sheets.dashboard
    → report_sheets.signals
    → report_sheets.weekly_actions
    → report_sheets.portfolio_state
    → report_sheets.harvest_log
    → report_sheets.logs

OUTPUT: universal_data (ready for Phase 4 - Sheets Writer)
```

---

## 🧪 Testing Strategy (per module)

### Test 1: Budget Calculation
```
Scenarios:
- S2 at target (gap = 0) → budget = 0
- S2 underweight (gap > 0) → budget calculated correctly
- S2 overweight (gap < 0) → budget = 0
- Carry-forward enabled → accrued carry added
- Caps applied → min(base, transfer_cap, weekly_cap)
```

### Test 2: Health Checks
```
Scenarios:
- All gates pass → Health = 4, Pass = TRUE
- 3 gates pass → Health = 3, Pass = FALSE
- All gates fail → Health = 0, Pass = FALSE
- Missing indicator data → Pass = FALSE, warning logged
- ATR override used → correct threshold applied
```

### Test 3: Harvest Triggers
```
Scenarios:
- Position in loss → skip harvest
- H1 fires → 10% trim
- H2 fires → 15% trim
- H3 fires (both conditions) → 25% trim
- Floor violation → trim scaled down
- Cooldown active → Action = SKIP
- Sleeve cap exceeded → proportional scaling
```

### Test 4: Action Generation
```
Scenarios:
- No budget + no trims → all NO_ACTION
- Budget available, all ETFs fail health → NO_ACTION + carry forward
- Budget available, 2 ETFs pass health → both get BUY actions
- Harvest trigger + buy eligible → both actions executed
- Single ETF cap hit → skip excess allocation
- Tag cap hit → skip affected ETFs
```

### Test 5: Output Formatting
```
Scenarios:
- All sheets have correct column structure
- Dashboard metrics calculated correctly
- Portfolio state updated with projected positions
- Signals include all required indicators
- Logs contain all system events
```

---

## 📋 Configuration Dependencies

**From CONFIG Sheet (used by Phase 3):**
```
Section A - System Parameters:
- S2_Target_%
- Weeks_to_Glide
- Enable_Carry_Forward

Section B - Risk Controls:
- DriftBand_%
- CoreFloor_%
- ATR_Ceiling_%
- Single_ETF_Max_%

Section C - ETF Lineup:
- ETF targets (Target_%_of_S2)
- ATR overrides (per ETF)
- Tags (for sector caps)

Section D - Harvest Settings (implicitly in config):
- H1/H2/H3 trim %
- MaxTrimPerETF_%
- WeeklyHarvestCap_%
- Cooldown (max harvests per 4 weeks)
```

---

## ⚠️ Critical Design Decisions

1. **Weekly timeframe only**: All health/harvest checks use 1W data, not 1h or 1d
2. **Binary pass/fail**: No partial credit for health gates
3. **Harvest before buy**: Trims are processed first, then buys with remaining budget
4. **No same-week netting**: Harvest proceeds don't add to buy budget
5. **Floors are hard limits**: Never violate, even if it means no trim
6. **Caps are proactive**: Check before creating action, not after
7. **Carry-forward is additive**: Unspent budget accumulates (within caps)
8. **Cooldown overrides triggers**: If active, skip harvest even if triggered

---

This design gives you a complete blueprint for Phase 3. Ready to implement when you are! 🚀