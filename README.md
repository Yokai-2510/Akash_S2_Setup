
---
## 🎯 Summary
> Build a weekly auto-decision system that **allocates a pool of capital** across multiple ETFs **based on signals**, executes buys/trims automatically (GTTs), and keeps portfolio risk & exposure balanced.

---

## 🧩 The Core Parts (and how they connect)

### 1️⃣ Data Fetch

**Purpose:** Get weekly prices for all ETFs.  
**What you do:**

- Pull Friday closes for each ETF.
- Store OHLCV data (Open, High, Low, Close, Volume).
- Needed for indicators (RSI, TSI, VWMA, ATR%).

**Output:** price history DataFrame.

---

### 2️⃣ Indicators Calculation

**Purpose:** Turn prices into _signals_.  
**What you do:**

- Compute RSI, TSI, VWMA slope, ATR%.

- Check if ETF passes “health” filters:

    - RSI > 50
    - TSI > signal
    - VWMA slope > 0
    - ATR% below ceiling        

**Output:** a table of ETFs with current signal states — green/red flags basically.

---

### 3️⃣ ETF Filtering / Ranking

**Purpose:** Choose _which ETFs_ are tradeable this week.  
**Logic:**

- Keep ETFs that pass all filters (“healthy”).    
- Optionally rank by strongest momentum or other metric.
- Remove ones on cooldown / above weight caps.

**Output:** shortlist of ETFs eligible for new buys.

---

### 4️⃣ Portfolio Allocation Logic

**Purpose:** Decide _how much_ to allocate to each.

Now comes the “target vs current weight” stuff:

- Each ETF has a **target weight** (client defines, like 10% of total capital).    
- The system tracks the **current weight** (how much money is actually invested in that ETF).
- The **Gap_to_Target** = Target − Current.
    - If gap > 0 → needs more buying (underweight).
    - If gap < 0 → might need trimming (overweight).


**Client knobs** like `Weekly Transfer Cap %`, `Base Trim %`, etc. control how much to adjust per week.

**Output:** amount of capital to deploy this week per ETF.

---

### 5️⃣ Order Planning (the “trade” step)

**Purpose:** Generate the _action plan_ — the trades to do.  
**Logic:**

- For each eligible ETF, plan a **GTT Buy** order if underweight and signal = healthy.    
    - Entry price = current close − 0.5×ATR (risk cushion).

- If an ETF exceeds trims rules or hits profit band → plan **Trim (Sell)** action.

- Respect caps (max per ETF, per week, per tag).

**Output:** list of orders with amounts, prices, reasons — written to Excel `actions` sheet.

---

### 6️⃣ Monday Mix (the actual execution)

**Purpose:** Apply the plan.  
**Logic:**

- Monday morning, system or human reviews generated GTT list and executes on broker.
    
- The model’s job is _just to prepare_ them — not actually send to broker (unless you integrate APIs).
    

---

### 7️⃣ Tracking & Logging

**Purpose:** Keep history, measure effectiveness.  
**What you do:**

- Record what was bought/sold each week.
- Track capital allocation and signals over time.
- Compare real vs target weights, update Excel sheets.
- Enables performance tracking, debugging, and compliance.    

---

## 🧠 Backtesting fits in here

It’s _offline simulation_ of this **entire weekly pipeline** using historical data.

You simulate as if the system had existed 2 years ago:

- Run each week’s data through indicator → filter → allocation → trades.
- Apply the same caps and rules.    
- Track how capital evolved (profit, drawdown, hit rate of signals).


**Goal:**  
See whether these rules and knobs would’ve made money, avoided risk, and behaved as expected.

That’s the “backtest”.

---

## 🧭 Simplified Flow Summary

```
(1) Fetch weekly prices for all ETFs
(2) Compute indicators: RSI, TSI, VWMA slope, ATR%
(3) Apply health gates
      - RSI > 50
      - TSI > signal
      - VWMA slope > 0
      - ATR% < ceiling
(4) Score ETFs: must pass ≥ 2 of 3 key health criteria
(5) Filter eligible ETFs
(6) Compute budget:
      Weekly_SIP_Budget = min(
          Weekly_Transfer_Cap_% × Total_Capital,
          S2_Weekly_Budget_Cap_% × Total_Capital
      )
(7) Allocate budget across eligible ETFs
      - Weight by Target% or health rank
      - Apply Single-ETF and Tag caps
(8) Generate GTT Buy orders:
      - Entry price = Friday close – 0.5 × ATR
      - Limit price = entry_price
(9) Record trades & logs → Excel
(10) Apply cooldowns (no repeat buys within 2–3 weeks)
---





## 🏛️ System Architecture Overview

```
S2_Trading_System/
│
	├── main.xpy                           # Entry point - orchestrates all phases
│
├── configs/                          # All configuration files
│   ├── system_config.json           # Infrastructure settings (URLs, cache, debug flags)
│   ├── strategy_config.json         # Trading logic (indicators, risk params, ETF universe)
│   └── credentials.json             # API keys (Upstox, Google Sheets)
│
├── utils/                            # Shared utilities
│   ├── __init__.py
│   ├── initialize_data.py           # Creates universal_data structure
│   ├── logger.py                    # Tagged logging system
│   └── validators.py                # Config validation helpers
│
├── connectors/                       # External system interfaces
│   ├── __init__.py
│   ├── sheets_reader.py             # Read from Google Sheets (CONFIG, STATE)
│   └── sheets_writer.py             # Write to Google Sheets (all output sheets)
│
├── data_pipeline/                    # Phase 2: Market data acquisition
│   ├── __init__.py
│   ├── upstox_auth.py               # Authentication & token management
│   ├── instrument_fetcher.py        # ETF master list (NSE + Upstox)
│   ├── ohlcv_downloader.py          # Historical price data sync
│   └── indicator_calculator.py      # Technical indicators (RSI, TSI, VWMA, ATR)
│
├── decision_engine/                  # Phase 3: Strategy logic
│   ├── __init__.py
│   ├── calculate_budget.py          # Weekly capital allocation
│   ├── check_health.py              # Health gate evaluation (4 conditions)
│   ├── check_harvest.py             # Profit-taking triggers (H1/H2/H3)
│   ├── generate_actions.py          # BUY/TRIM/NO_ACTION decisions
│   └── format_outputs.py            # Transform to sheet-ready DataFrames
│
├── live_update/                      # Phase 5: Excel change detection & auto-execution
│   ├── __init__.py
│   ├── trigger_monitor.py           # Polls Excel for UPDATE_TRIGGER flag
│   ├── change_detector.py           # Identifies what changed in CONFIG
│   ├── pipeline_orchestrator.py     # Decides which modules to re-run
│   └── status_manager.py            # Updates control cells in Excel
│
├── source/                           # Data storage
│   ├── credentials.json             # (gitignored)
│   ├── access_token.json            # Cached Upstox token
│   ├── state_cache.json             # Previous Excel state snapshot
│   ├── data/
│   │   ├── etf_instrument_master.csv
│   │   └── indicator_data.parquet
│   └── etf_ohlcv_data/
│       ├── NIFTYBEES_1m_history.json
│       ├── BANKBEES_1m_history.json
│       └── ...
│
├── logs/
│   └── trading_system.log           # Persistent log file
│
├── tests/                            # Unit tests (optional)
│   ├── test_budget.py
│   ├── test_health.py
│   └── ...
│
└── requirements.txt                  # Python dependencies
```

---

## 📦 Module Dependency Graph

```
main.py
  │
  ├─> utils.initialize_data          # Creates universal_data
  │
  ├─> connectors.sheets_reader        # Loads CONFIG & STATE from Excel
  │     └─> (reads Google Sheets)
  │
  ├─> live_update.trigger_monitor     # PHASE 5: Check if UPDATE_TRIGGER=TRUE
  │     │
  │     └─> live_update.change_detector
  │           └─> live_update.pipeline_orchestrator
  │                 │
  │                 ├─> data_pipeline.* (if ETF lineup changed)
  │                 └─> decision_engine.* (if config/portfolio changed)
  │
  ├─> data_pipeline.upstox_auth       # PHASE 2
  ├─> data_pipeline.instrument_fetcher
  ├─> data_pipeline.ohlcv_downloader
  ├─> data_pipeline.indicator_calculator
  │
  ├─> decision_engine.calculate_budget # PHASE 3
  ├─> decision_engine.check_health
  ├─> decision_engine.check_harvest
  ├─> decision_engine.generate_actions
  ├─> decision_engine.format_outputs
  │
  └─> connectors.sheets_writer        # PHASE 4: Write results back to Excel
```

---

## 🔧 Configuration Files Detailed Structure

### `configs/system_config.json`

```json
{
  "system": {
    "project_name": "S2 Trading System",
    "version": "2.0",
    "log_level": "INFO",
    "execution_mode": "daemon"
  },

  "debug_controls": {
    "force_fresh_login": false,
    "force_nse_refresh": false,
    "force_upstox_refresh": false,
    "force_ohlcv_resync": false,
    "force_indicator_recalc": false,
    "enable_playwright_headless": true,
    "save_raw_api_responses": true,
    "mock_mode": false
  },

  "data_sources": {
    "nse_api_url": "https://www.nseindia.com/api/etf",
    "upstox_instruments_url": "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz",
    "upstox_historical_api": "https://api.upstox.com/v3/historical-candle",
    "upstox_login_dialog": "https://api-v2.upstox.com/login/authorization/dialog",
    "upstox_token_api": "https://api-v2.upstox.com/login/authorization/token"
  },

  "data_acquisition": {
    "full_history_start_date": "2022-01-01",
    "api_fetch_chunk_days": 28,
    "api_rate_limit_delay_seconds": 0.5,
    "max_retries": 3,
    "request_timeout_seconds": 30
  },

  "cache_policies": {
    "instrument_master_cache_days": 7,
    "access_token_expiry_time": "03:30:00",
    "ohlcv_incremental_sync": true,
    "indicator_snapshot_cache_hours": 24
  },

  "fallback_behavior": {
    "nse_failure": "use_upstox_only",
    "upstox_failure": "abort_pipeline",
    "single_etf_failure": "skip_and_continue",
    "indicator_calc_failure": "skip_etf"
  },

  "paths": {
    "credentials_file": "configs/credentials.json",
    "token_cache_file": "source/access_token.json",
    "state_cache_file": "source/state_cache.json",
    "instrument_master_file": "source/data/etf_instrument_master.csv",
    "ohlcv_data_dir": "source/etf_ohlcv_data",
    "indicator_history_file": "source/data/indicator_data.parquet",
    "log_file": "logs/trading_system.log"
  },

  "google_sheets": {
    "spreadsheet_id": "YOUR_SHEET_ID_HERE",
    "poll_interval_seconds": 30,
    "connection_timeout_seconds": 10
  }
}
```

---

### `configs/strategy_config.json`

```json
{
  "universe": {
    "etfs_to_track": [
      "NIFTYBEES",
      "BANKBEES",
      "GOLDBEES",
      "JUNIORBEES",
      "ITBEES",
      "SILVERBEES",
      "MON100",
      "CPSEETF"
    ],
    "timeframes": ["1h", "1d", "1W"],
    "primary_timeframe": "1W"
  },

  "indicators": {
    "enabled_indicators": [
      {"name": "ema", "params": {"length": 50}},
      {"name": "ema", "params": {"length": 200}},
      {"name": "vwma", "params": {"length": 20}},
      {"name": "rsi", "params": {"length": 14}},
      {"name": "tsi", "params": {"fast": 25, "slow": 13, "signal": 7}},
      {"name": "atr", "params": {"length": 14}},
      {"name": "bbands", "params": {"length": 20, "std": 2.0}}
    ]
  },

  "allocation_rules": {
    "s2_target_percent": 34.0,
    "weeks_to_glide": 52,
    "enable_carry_forward": true,
    "weekly_transfer_cap_percent": 5.0,
    "s2_weekly_budget_cap_percent": 1.25
  },

  "risk_controls": {
    "drift_band_percent": 10.0,
    "core_floor_percent": 70.0,
    "default_atr_ceiling_percent": 2.0,
    "single_etf_max_percent": 35.0,
    "max_trim_per_etf_percent": 25.0,
    "weekly_harvest_cap_percent": 12.0
  },

  "health_gates": {
    "required_score": 4,
    "gate_1_tsi_above_signal": true,
    "gate_2_rsi_above_50": true,
    "gate_3_vwma_slope_positive": true,
    "gate_4_atr_below_ceiling": true
  },

  "harvest_triggers": {
    "h1_stretch": {
      "enabled": true,
      "rsi_threshold": 70,
      "trim_percent": 10.0
    },
    "h2_volspike": {
      "enabled": true,
      "atr_percentile": 80,
      "lookback_weeks": 26,
      "trim_percent": 15.0
    },
    "h3_breakdown": {
      "enabled": true,
      "trigger": "tsi_cross_down",
      "trim_percent": 15.0
    }
  },

  "execution_params": {
    "gtt_entry_atr_multiplier": 0.5,
    "gtt_validity_days": 7,
    "round_down_units": true
  }
}
```

---

## 📊 Universal Data Structure (Complete Schema)

```python
universal_data = {
    # ================================================================
    # SYSTEM CONTEXT
    # ================================================================
    "system": {
        "project_root": str,              # Absolute path to project directory
        "run_timestamp": str,             # ISO format: "2024-11-20T10:30:00"
        "status": str,                    # INITIALIZING / RUNNING / SUCCESS / ERROR
        "execution_mode": str,            # "daemon" / "single_run" / "test"
        "debug_flags": {                  # From system_config.json
            "force_fresh_login": bool,
            "force_nse_refresh": bool,
            "force_ohlcv_resync": bool,
            # ... all debug flags
        }
    },

    # ================================================================
    # CONFIGURATIONS (Merged from JSON + Excel)
    # ================================================================
    "configs": {
        "system_settings": dict,          # Full system_config.json content
        "strategy_settings": dict,        # Full strategy_config.json content
        
        # From Excel CONFIG sheet:
        "system_params": pd.DataFrame,    # Columns: Parameter, Value, Unit, Description
        "etf_lineup": pd.DataFrame,       # Columns: ETF_ID, Ticker, Enabled, Target_%, ATR_Override_%
        
        # Convenience extracts:
        "universe_settings": {
            "etfs_to_track": list,        # ["NIFTYBEES", "BANKBEES", ...]
            "timeframes_to_calculate": list  # ["1h", "1d", "1W"]
        },
        "indicator_settings": list        # List of enabled indicators with params
    },

    # ================================================================
    # PORTFOLIO STATE (From Excel STATE sheet)
    # ================================================================
    "portfolio_state": {
        "holdings": pd.DataFrame,         # Columns: ETF_ID, Ticker, Units, Avg_Buy_Price, 
                                          #          Current_Price, Market_Value, Current_%, 
                                          #          Target_%, Gap_%, Status
        
        "summary": {
            "total_s2_value": float,      # Sum of all holdings
            "current_s2_weight_pct": float,  # S2 allocation as % of total portfolio
            "num_holdings": int,
            "last_updated": str           # Timestamp
        }
    },

    # ================================================================
    # MARKET DATA (Phase 2 outputs)
    # ================================================================
    "market_data": {
        "etf_master_list": pd.DataFrame,  # Columns: nse_symbol, underlying_asset, isin,
                                          #          upstox_instrument_key, upstox_name
        
        "ohlcv_file_paths": dict,         # {symbol: file_path}
                                          # e.g., {"NIFTYBEES": "source/etf_ohlcv_data/NIFTYBEES_1m_history.json"}
        
        "indicator_snapshot_df": pd.DataFrame,  # Columns: ETF, Timeframe, Timestamp,
                                                #          TSI_25_13_7, TSIe_25_13_7, RSI_14,
                                                #          VWMA_20, ATRp_14, EMA_50, EMA_200, ...
                                                # One row per ETF-Timeframe combination
        
        "indicator_history_path": str     # Path to full parquet file (for analysis)
    },

    # ================================================================
    # ANALYSIS RESULTS (Phase 3 intermediate outputs)
    # ================================================================
    "analysis": {
        "weekly_budget": float,           # Available capital for this week
        "gap_to_target": float,           # How much underweight S2 is
        "accrued_carry": float,           # Unused budget from previous weeks
        
        "health_matrix_df": pd.DataFrame, # Columns: ETF, TSI, TSI_Signal, RSI, VWMA_Slope,
                                          #          ATR%, ATR_Ceiling%, Gate_1_TSI, Gate_2_RSI,
                                          #          Gate_3_VWMA, Gate_4_ATR, Health_Score, Pass
        
        "harvest_triggers_df": pd.DataFrame,  # Columns: ETF, In_Profit, Trigger, RSI, TSI,
                                              #          TSI_Signal, ATR%, Base_Trim_%, 
                                              #          Floor_Adjusted_Trim_%, Units_to_Trim,
                                              #          Trim_Value_₹, Action
    },

    # ================================================================
    # EXECUTION PLAN (Phase 3 final output)
    # ================================================================
    "execution_plan": {
        "weekly_actions_df": pd.DataFrame  # Columns: Week_Date, ETF_ID, ETF, Action,
                                           #          Units, Price, Amount_₹, Reason,
                                           #          Pre_%, Post_%, Trigger, Status
                                           # Action: BUY / TRIM / NO_ACTION
    },

    # ================================================================
    # FORMATTED SHEETS (Phase 3 → sheets_writer)
    # ================================================================
    "report_sheets": {
        "dashboard": pd.DataFrame,        # Summary metrics table
        "config": pd.DataFrame,           # Pass-through of CONFIG sheet
        "portfolio_state": pd.DataFrame,  # Enhanced STATE with projections
        "signals": pd.DataFrame,          # Latest technical indicators
        "weekly_actions": pd.DataFrame,   # This week's trade plan
        "harvest_log": pd.DataFrame,      # Append-only trim history
        "logs": pd.DataFrame              # System execution logs
    },

    # ================================================================
    # PHASE 5: CHANGE TRACKING
    # ================================================================
    "change_detection": {
        "update_trigger": bool,           # From Excel SYSTEM_CONTROL
        "last_run_timestamp": str,
        "cached_state_hash": dict,        # Previous config/lineup/portfolio hashes
        
        "changes_detected": {
            "config_changed": bool,
            "etf_lineup_changed": bool,
            "portfolio_changed": bool,
            "force_full_refresh": bool
        },
        
        "modules_to_rerun": list          # ["data_pipeline", "decision_engine", ...]
    },

    # ================================================================
    # AUTHENTICATION & TOKENS
    # ================================================================
    "access_token": str,                  # Upstox access token (cached)
    "token_expiry": str                   # ISO format timestamp
}
```

---

## 🔄 Phase-by-Phase Data Flow

### **PHASE 1: INITIALIZATION**

**Modules:**
- `utils/initialize_data.py`
- `connectors/sheets_reader.py`

**Input:**
- `configs/system_config.json`
- `configs/strategy_config.json`
- `configs/credentials.json`
- Google Sheets → CONFIG tab
- Google Sheets → STATE tab

**Output:**
- `universal_data` structure populated with:
  - `system.*`
  - `configs.*`
  - `portfolio_state.*`

**Key Functions:**
```python
initialize_universal_data(project_root: str) -> Dict[str, Any]
load_config_and_portfolio(universal_data: Dict) -> Dict[str, Any]
```

---

### **PHASE 2: DATA PIPELINE**

**Modules:**
- `data_pipeline/upstox_auth.py`
- `data_pipeline/instrument_fetcher.py`
- `data_pipeline/ohlcv_downloader.py`
- `data_pipeline/indicator_calculator.py`

**Input:**
- `universal_data['configs']`
- External APIs: Upstox, NSE

**Output:**
- `universal_data['market_data']` populated with:
  - `etf_master_list`
  - `ohlcv_file_paths`
  - `indicator_snapshot_df`

**Cache Files Created:**
- `source/access_token.json`
- `source/data/etf_instrument_master.csv`
- `source/etf_ohlcv_data/*.json` (one per ETF)
- `source/data/indicator_data.parquet`

**Key Functions:**
```python
process_authentication(universal_data: Dict) -> Dict
sync_instrument_master(universal_data: Dict) -> Dict
process_ohlcv_sync(universal_data: Dict) -> Dict
process_indicator_calculation(universal_data: Dict) -> Dict
```

---

### **PHASE 3: DECISION ENGINE**

**Modules:**
- `decision_engine/calculate_budget.py`
- `decision_engine/check_health.py`
- `decision_engine/check_harvest.py`
- `decision_engine/generate_actions.py`
- `decision_engine/format_outputs.py`

**Input:**
- `universal_data['configs']`
- `universal_data['portfolio_state']`
- `universal_data['market_data']['indicator_snapshot_df']`

**Output:**
- `universal_data['analysis']` populated with:
  - `weekly_budget`
  - `health_matrix_df`
  - `harvest_triggers_df`
- `universal_data['execution_plan']` populated with:
  - `weekly_actions_df`
- `universal_data['report_sheets']` populated with all formatted sheets

**Key Functions:**
```python
calculate_weekly_budget(universal_data: Dict) -> Dict
run_health_checks(universal_data: Dict) -> Dict
find_harvest_triggers(universal_data: Dict) -> Dict
generate_weekly_actions(universal_data: Dict) -> Dict
format_all_sheets(universal_data: Dict) -> Dict
```

---

### **PHASE 4: OUTPUT WRITER**

**Modules:**
- `connectors/sheets_writer.py`

**Input:**
- `universal_data['report_sheets']`

**Output:**
- Google Sheets updated:
  - DASHBOARD (overwrite)
  - STATE (overwrite)
  - SIGNALS (overwrite)
  - WEEKLY_ACTIONS (overwrite)
  - HARVEST_LOG (append)
  - LOGS (append)

**Key Functions:**
```python
write_all_sheets_to_excel(universal_data: Dict) -> None
```

---

### **PHASE 5: LIVE UPDATE SYSTEM**

**Modules:**
- `live_update/trigger_monitor.py`
- `live_update/change_detector.py`
- `live_update/pipeline_orchestrator.py`
- `live_update/status_manager.py`

**Input:**
- Google Sheets → SYSTEM_CONTROL tab
  - `UPDATE_TRIGGER` cell
  - `RUN_STATUS` cell
- `source/state_cache.json` (previous run state)

**Output:**
- Decides which phases to re-run
- Updates `SYSTEM_CONTROL` tab:
  - `UPDATE_TRIGGER` → FALSE
  - `RUN_STATUS` → SUCCESS/ERROR
  - `LAST_RUN_DATE` → timestamp
  - `ERROR_MESSAGE` → error details (if failed)

**Key Functions:**
```python
monitor_excel_trigger(universal_data: Dict, poll_interval: int) -> None
detect_changes(universal_data: Dict) -> ChangeReport
execute_incremental_update(universal_data: Dict) -> Dict
update_control_cells(universal_data: Dict, updates: Dict) -> None
```

---

## 🎛️ Excel Sheets Structure

### Sheet 1: **SYSTEM_CONTROL** (NEW)

| Parameter | Value | Last_Updated |
|-----------|-------|--------------|
| UPDATE_TRIGGER | FALSE | 2024-11-20 10:30:00 |
| FORCE_FULL_REFRESH | FALSE | - |
| RUN_STATUS | SUCCESS | 2024-11-20 10:35:00 |
| ERROR_MESSAGE | - | - |
| LAST_RUN_DATE | 2024-11-20 10:35:00 | - |

**Purpose:** Control panel for triggering pipeline runs

---

### Sheet 2: **CONFIG**

**Section A: System Parameters**

| Parameter | Value | Unit | Description |
|-----------|-------|------|-------------|
| S2_Target_% | 34.0 | % | Target allocation from Asset Allocator |
| Weeks_to_Glide | 52 | weeks | Spread gap over this many weeks |
| Enable_Carry_Forward | TRUE | boolean | Carry unused budget to next week |
| Weekly_Transfer_Cap_% | 5.0 | % | Max % of capital to move weekly |
| S2_Weekly_Budget_Cap_% | 1.25 | % | Max % of S2 to deploy weekly |

**Section B: Risk Controls**

| Parameter | Value | Unit | Description |
|-----------|-------|------|-------------|
| DriftBand_% | 10.0 | % | Tolerance before action |
| CoreFloor_% | 70.0 | % | Min % of target |
| ATR_Ceiling_% | 2.0 | % | Default volatility limit |
| Single_ETF_Max_% | 35.0 | % | Max single position |
| MaxTrimPerETF_% | 25.0 | % | Max trim per harvest |
| WeeklyHarvestCap_% | 12.0 | % | Max weekly profit taking |

**Section C: ETF Lineup**

| ETF_ID | Ticker | Enabled | Target_% | ATR_Override_% | Tags | Notes |
|--------|--------|---------|----------|----------------|------|-------|
| ETF_01 | NIFTYBEES | TRUE | 40.0 | - | Core,Broad | Nifty 50 Index |
| ETF_02 | BANKBEES | TRUE | 20.0 | 2.5 | Core,Financials | Bank Nifty |
| ETF_03 | GOLDBEES | TRUE | 15.0 | 3.0 | Satellite,Commodity | Gold ETF |
| ETF_04 | JUNIORBEES | TRUE | 10.0 | - | Satellite,Midcap | Nifty Next 50 |
| ETF_05 | ITBEES | TRUE | 6.0 | 2.8 | Satellite,Sector | IT Sector |
| ETF_06 | SILVERBEES | TRUE | 6.0 | 3.5 | Satellite,Commodity | Silver ETF |
| ETF_07 | MON100 | FALSE | 3.0 | - | Satellite | Momentum (disabled) |

---

### Sheet 3: **STATE**

| ETF_ID | Ticker | Units | Avg_Buy_Price | Current_Price | Market_Value | Current_% | Target_% | Gap_% | Status | Projected_Post_% |
|--------|--------|-------|---------------|---------------|--------------|-----------|----------|-------|--------|------------------|
| ETF_01 | NIFTYBEES | 625 | 158.40 | 165.50 | 103437.50 | 38.5 | 40.0 | -1.5 | NEAR | 39.2 |
| ETF_02 | BANKBEES | 160 | 405.00 | 420.00 | 67200.00 | 25.0 | 20.0 | +5.0 | OVER | 24.1 |
| ETF_03 | GOLDBEES | 480 | 46.50 | 48.00 | 23040.00 | 8.6 | 15.0 | -6.4 | UNDER | 10.2 |

---

### Sheet 4: **SIGNALS**

| Week_Date | ETF | TSI | TSI_Signal | RSI | VWMA_Slope | ATR% | ATR_Ceiling% | Health_Score | Pass |
|-----------|-----|-----|------------|-----|------------|------|--------------|--------------|------|
| 2024-11-18 | NIFTYBEES | 12.5 | 10.2 | 58 | 0.8 | 1.8 | 2.0 | 4 | TRUE |
| 2024-11-18 | BANKBEES | -5.2 | 2.1 | 45 | -0.3 | 2.2 | 2.5 | 1 | FALSE |
| 2024-11-18 | GOLDBEES | 8.3 | 6.5 | 52 | 0.5 | 2.9 | 3.0 | 4 | TRUE |

---

### Sheet 5: **WEEKLY_ACTIONS**

| Week_Date | ETF_ID | ETF | Action | Units | Price | Amount_₹ | Reason | Pre_% | Post_% | Trigger | Status |
|-----------|--------|-----|--------|-------|-------|----------|--------|-------|--------|---------|--------|
| 2024-11-18 | ETF_03 | GOLDBEES | BUY | 125 | 47.50 | 5937.50 | UNDER+H4 | 8.6 | 10.2 | - | PLANNED |
| 2024-11-18 | ETF_02 | BANKBEES | TRIM | 25 | 420.00 | 10500.00 | H1_Stretch | 25.0 | 24.1 | RSI>70 | PLANNED |
| 2024-11-18 | ETF_01 | NIFTYBEES | NO_ACTION | 0 | - | 0 | NEAR | 38.5 | 38.5 | - | SKIPPED |

---

### Sheet 6: **HARVEST_LOG**

| Timestamp | ETF | Trigger | Units | Price | Amount_₹ | Signal_Snapshot |
|-----------|-----|---------|-------|-------|----------|-----------------|
| 2024-11-18 10:35:00 | BANKBEES | H1_Stretch | 25 | 420.00 | 10500.00 | RSI:72 TSI:8.2/6.5 ATR:2.2% |
| 2024-11-11 10:22:00 | GOLDBEES | H2_VolSpike | 40 | 47.80 | 1912.00 | RSI:58 TSI:12.1/10.3 ATR:3.2% |

---

### Sheet 7: **DASHBOARD**

| Metric | Value |
|--------|-------|
| Total S2 Value (₹) | 268,500.00 |
| Current S2 Weight (%) | 33.2 |
| Target S2 Weight (%) | 34.0 |
| Gap to Target (₹) | 6,480.00 |
| Weekly Budget (₹) | 3,356.25 |
| Accrued Carry (₹) | 0.00 |
| ETFs Passing Health | 4 |
| Buy Actions | 2 |
| Trim Actions | 1 |

---

### Sheet 8: **LOGS**

| Timestamp | Module | Level | Message | Tags |
|-----------|--------|-------|---------|------|
| 2024-11-18 10:30:05 | Budget Calculator | INFO | Weekly budget: ₹3,356.25 | DECISION,BUDGET |
| 2024-11-18 10:30:12 | Health Checker | INFO | ETFs passing health: 4 | DECISION,HEALTH |
| 2024-11-18 10:30:18 | Harvest Checker | INFO | Harvest triggers: 1 trims | DECISION,HARVEST |
| 2024-11-18 10:30:25 | Action Generator | INFO | Actions: 2 buys, 1 trims | DECISION,ACTIONS |

---

## 🚀 Execution Modes

### Mode 1: Daemon (Continuous Monitoring)

```python
# main.py

def main():
    """Run in daemon mode - continuously monitor Excel for changes."""
    
    universal_data = initialize_universal_data(project_root)
    
    from live_update.trigger_monitor import monitor_excel_trigger
    
    # Infinite loop - checks Excel every 30 seconds
    monitor_excel_trigger(universal_data, poll_interval_seconds=30)
```

**Use Case:** Production server running 24/7

---

### Mode 2: Single Run (One-Shot)

```python
# main.py

def main():
    """Bypass all caches - full fresh run."""
    
    universal_data = initialize_universal_data(project_root)
    
    # Override debug flags
    universal_data['system']['debug_flags']['force_fresh_login'] = True
    universal_data['system']['debug_flags']['force_nse_refresh'] = True
    universal_data['system']['debug_flags']['force_ohlcv_resync'] = True
    universal_data['system']['debug_flags']['force_indicator_recalc'] = True
    
    # Run full pipeline with all caches bypassed
    run_full_pipeline(universal_data)
```

**Use Case:** Troubleshooting, data corruption recovery, initial setup

---

## 🧩 Module Interaction Patterns

### Pattern 1: Standard Data Flow (Full Pipeline)

```
┌─────────────────────────────────────────────────────────────┐
│                         MAIN.PY                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: INITIALIZATION                                    │
│  ├─ utils.initialize_data                                   │
│  └─ connectors.sheets_reader                                │
│       └─ Reads: CONFIG, STATE from Google Sheets            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: DATA PIPELINE                                     │
│  ├─ data_pipeline.upstox_auth                               │
│  │    └─ Output: access_token                               │
│  ├─ data_pipeline.instrument_fetcher                        │
│  │    └─ Output: etf_master_list                            │
│  ├─ data_pipeline.ohlcv_downloader                          │
│  │    └─ Output: ohlcv_file_paths (JSON files)              │
│  └─ data_pipeline.indicator_calculator                      │
│       └─ Output: indicator_snapshot_df                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: DECISION ENGINE                                   │
│  ├─ decision_engine.calculate_budget                        │
│  │    └─ Output: weekly_budget, accrued_carry               │
│  ├─ decision_engine.check_health                            │
│  │    └─ Output: health_matrix_df                           │
│  ├─ decision_engine.check_harvest                           │
│  │    └─ Output: harvest_triggers_df                        │
│  ├─ decision_engine.generate_actions                        │
│  │    └─ Output: weekly_actions_df                          │
│  └─ decision_engine.format_outputs                          │
│       └─ Output: report_sheets (all formatted DataFrames)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: OUTPUT WRITER                                     │
│  └─ connectors.sheets_writer                                │
│       └─ Writes: All sheets back to Google Sheets           │
└─────────────────────────────────────────────────────────────┘
```

---

### Pattern 2: Incremental Update (Phase 5 Smart Re-run)

```
┌─────────────────────────────────────────────────────────────┐
│              CLIENT MODIFIES EXCEL CONFIG                   │
│              Sets UPDATE_TRIGGER = TRUE                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  live_update.trigger_monitor                                │
│  └─ Polls Excel every 30s                                   │
│     └─ Detects UPDATE_TRIGGER = TRUE                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  live_update.change_detector                                │
│  ├─ Loads cached state from state_cache.json                │
│  ├─ Reads current CONFIG from Excel                         │
│  └─ Compares → identifies what changed                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  live_update.pipeline_orchestrator                          │
│  Decision Matrix:                                           │
│                                                             │
│  IF config_changed (budget, risk params):                   │
│     └─ Re-run PHASE 3 only                                  │
│                                                             │
│  IF etf_lineup_changed (added/removed ETF):                 │
│     └─ Re-run PHASE 2 + PHASE 3                             │
│                                                             │
│  IF portfolio_changed (manual holdings update):             │
│     └─ Re-run PHASE 3 only                                  │
│                                                             │
│  IF force_full_refresh:                                     │
│     └─ Re-run ALL PHASES                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Execute Selected Phases                                    │
│  └─ Run minimal set of modules needed                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  live_update.status_manager                                 │
│  ├─ Update SYSTEM_CONTROL cells:                            │
│  │   ├─ UPDATE_TRIGGER → FALSE                              │
│  │   ├─ RUN_STATUS → SUCCESS                                │
│  │   └─ LAST_RUN_DATE → current timestamp                   │
│  └─ Save new state to state_cache.json                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Detailed Module Specifications

### **utils/initialize_data.py**

```python
"""
Creates the universal_data structure that flows through entire pipeline.
Loads both system and strategy configurations.
"""

def initialize_universal_data(project_root: str) -> Dict[str, Any]:
    """
    Initialize empty universal_data structure and load configs.
    
    Returns:
        Complete universal_data dict with configs loaded
    """
    
def _load_system_config(project_root: str) -> dict:
    """Load configs/system_config.json"""
    
def _load_strategy_config(project_root: str) -> dict:
    """Load configs/strategy_config.json"""
    
def _validate_configs(system_config: dict, strategy_config: dict) -> None:
    """Validate required fields are present"""
```

---

### **utils/logger.py**

```python
"""
Tagged logging system with console + file output.
Supports log levels: INFO, WARNING, ERROR, CRITICAL.
Tags enable filtering (e.g., [PHASE_2,OHLCV,ERROR]).
"""

class TaggedLogger:
    def info(self, msg: str, tags: List[str] = None)
    def warning(self, msg: str, tags: List[str] = None)
    def error(self, msg: str, tags: List[str] = None, exc_info: bool = False)
    def critical(self, msg: str, tags: List[str] = None, exc_info: bool = False)

def setup_logger() -> TaggedLogger:
    """Returns singleton logger instance"""
```

---

### **utils/validators.py**

```python
"""
Configuration validation helpers.
"""

def validate_system_config(config: dict) -> List[str]:
    """
    Returns list of validation errors (empty if valid).
    Checks: required keys, valid URLs, valid file paths, etc.
    """
    
def validate_strategy_config(config: dict) -> List[str]:
    """
    Validates strategy parameters.
    Checks: ETF list not empty, percentages sum to 100, etc.
    """
    
def validate_universal_data_structure(universal_data: dict) -> bool:
    """
    Ensures universal_data has all required top-level keys.
    """
```

---

### **connectors/sheets_reader.py**

```python
"""
Reads data from Google Sheets (CONFIG, STATE tabs).
"""

def load_config_and_portfolio(universal_data: Dict) -> Dict:
    """
    Main entry point - loads both CONFIG and STATE sheets.
    Populates universal_data['configs'] and universal_data['portfolio_state'].
    """
    
def read_config_sheet(universal_data: Dict) -> pd.DataFrame:
    """Read CONFIG sheet, parse into system_params and etf_lineup"""
    
def read_state_sheet(universal_data: Dict) -> pd.DataFrame:
    """Read STATE sheet, parse into holdings DataFrame"""
    
def read_control_cells(universal_data: Dict) -> dict:
    """
    Read SYSTEM_CONTROL cells (UPDATE_TRIGGER, RUN_STATUS, etc.).
    Returns dict of control values.
    """
    
def _authenticate_gspread(universal_data: Dict):
    """Authenticate using service account credentials"""
    
def _open_spreadsheet(universal_data: Dict):
    """Open spreadsheet by ID from config"""
```

---

### **connectors/sheets_writer.py**

```python
"""
Writes analysis results back to Google Sheets.
"""

class GoogleSheetsWriter:
    def __init__(self, universal_data: Dict)
    
    def clear_and_write_sheet(self, sheet_name: str, df: pd.DataFrame) -> None:
        """Overwrite entire sheet with new data"""
        
    def append_to_sheet(self, sheet_name: str, df: pd.DataFrame) -> None:
        """Append rows to existing sheet (for logs, harvest history)"""
        
    def update_cell(self, sheet_name: str, cell: str, value: Any) -> None:
        """Update single cell value"""
        
    def update_range(self, sheet_name: str, cell_range: str, values: List[List]) -> None:
        """Update multiple cells at once"""

def write_all_sheets_to_excel(universal_data: Dict) -> None:
    """
    Main entry point - writes all report_sheets to Google Sheets.
    """
    
def update_control_cells(universal_data: Dict, updates: dict) -> None:
    """
    Update SYSTEM_CONTROL cells (UPDATE_TRIGGER, RUN_STATUS, etc.).
    """
```

---

### **data_pipeline/upstox_auth.py**

```python
"""
Handles Upstox authentication and token management.
Tokens expire daily at 3:30 AM IST.
"""

def process_authentication(universal_data: Dict) -> Dict:
    """
    Main entry point - ensures valid access token exists.
    Checks cache first, performs browser automation if needed.
    """
    
def _attempt_token_from_cache(cache_path: str, force_fresh: bool) -> Optional[str]:
    """Try loading cached token if not expired"""
    
def _is_token_expired() -> bool:
    """Check if past 3:30 AM IST expiry"""
    
def _execute_full_authentication(universal_data: Dict, creds: dict) -> str:
    """Perform full browser automation + token exchange"""
    
def _obtain_auth_code_via_browser(universal_data: Dict, creds: dict) -> str:
    """Use Playwright to automate login and capture auth code"""
    
def _exchange_code_for_access_token(universal_data: Dict, creds: dict, code: str) -> str:
    """Exchange authorization code for access token via API"""
```

---

### **data_pipeline/instrument_fetcher.py**

```python
"""
Fetches ETF master list from NSE and Upstox, merges them.
Creates mapping of ticker → instrument_key for API calls.
"""

def sync_instrument_master(universal_data: Dict) -> Dict:
    """
    Main entry point - creates/updates etf_instrument_master.csv.
    Respects cache expiry settings and force refresh flags.
    """
    
def _fetch_nse_data(universal_data: Dict) -> pd.DataFrame:
    """Fetch ETF list from NSE website (with session warmup)"""
    
def _fetch_upstox_data(universal_data: Dict) -> pd.DataFrame:
    """Download complete instrument master from Upstox CDN"""
    
def _merge_nse_upstox(nse_df: pd.DataFrame, upstox_df: pd.DataFrame) -> pd.DataFrame:
    """Merge both sources on ticker symbol"""
    
def _build_upstox_only_master(upstox_df: pd.DataFrame, universal_data: Dict) -> pd.DataFrame:
    """Fallback if NSE fails - use Upstox only for tracked ETFs"""
```

---

### **data_pipeline/ohlcv_downloader.py**

```python
"""
Downloads 1-minute historical OHLCV data from Upstox.
Implements intelligent incremental sync (only fetch new data).
"""

def process_ohlcv_sync(universal_data: Dict) -> Dict:
    """
    Main entry point - syncs OHLCV data for all tracked ETFs.
    Populates universal_data['market_data']['ohlcv_file_paths'].
    """
    
def _determine_fetch_range(cache_file: str, universal_data: Dict) -> Optional[Tuple[date, date]]:
    """
    Decides what date range to fetch based on cache state.
    Returns None if already up-to-date.
    """
    
def _fetch_ohlcv_in_chunks(universal_data: Dict, instrument_key: str, 
                           start_date: date, end_date: date) -> list:
    """Break large date range into manageable chunks"""
    
def _fetch_single_chunk(universal_data: Dict, instrument_key: str,
                        from_date: date, to_date: date) -> list:
    """Single API call to Upstox historical endpoint"""
    
def _append_to_cache_file(file_path: str, new_candles: list) -> None:
    """
    Append new data to cache file.
    CRITICAL: Sorts and deduplicates to handle reverse-chronological API responses.
    """
```

---

### **data_pipeline/indicator_calculator.py**

```python
"""
Calculates technical indicators using pandas-ta library.
Generates both snapshot (latest values) and full history.
"""

def process_indicator_calculation(universal_data: Dict) -> Dict:
    """
    Main entry point - calculates all indicators for all ETFs/timeframes.
    Populates universal_data['market_data']['indicator_snapshot_df'].
    """
    
def _load_ohlcv_file(file_path: str) -> pd.DataFrame:
    """Load and parse JSON cache file into DataFrame"""
    
def _resample_to_timeframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample 1-minute data to target timeframe (1h, 1d, 1W)"""
    
def _apply_all_indicators(df: pd.DataFrame, indicator_configs: list) -> pd.DataFrame:
    """Apply all enabled indicators from config using pandas-ta"""
    
def _extract_latest_snapshot(full_df: pd.DataFrame) -> pd.DataFrame:
    """Extract latest indicator values per ETF/timeframe"""
    
def _save_full_history(universal_data: Dict, full_df: pd.DataFrame) -> None:
    """Save complete indicator history to parquet for analysis"""
```

---

### **decision_engine/calculate_budget.py**

```python
"""
Calculates weekly capital allocation based on gap-to-target and glide path.
"""

def calculate_weekly_budget(universal_data: Dict) -> Dict:
    """
    Main entry point - computes available capital for deployment.
    Respects caps and carry-forward settings.
    Populates universal_data['analysis']['weekly_budget'].
    """
    
def _get_param(configs: dict, param_name: str, default=None):
    """Extract parameter from system_params DataFrame"""
```

---

### **decision_engine/check_health.py**

```python
"""
Evaluates health gates for each ETF (4 conditions).
Only ETFs with Health_Score=4 are eligible for buying.
"""

def run_health_checks(universal_data: Dict) -> Dict:
    """
    Main entry point - runs health evaluation for all ETFs.
    Populates universal_data['analysis']['health_matrix_df'].
    """
    
def _get_etf_atr_override(etf_lineup: pd.DataFrame, etf: str, default: float) -> float:
    """Get ETF-specific ATR ceiling or use default"""
    
def _calc_vwma_slope(snapshot: pd.DataFrame, etf: str) -> float:
    """Calculate VWMA slope (current week vs previous week)"""
```

---

### **decision_engine/check_harvest.py**

```python
"""
Identifies profit-taking opportunities based on H1/H2/H3 triggers.
Calculates trim amounts with floor protections.
"""

def find_harvest_triggers(universal_data: Dict) -> Dict:
    """
    Main entry point - checks for harvest triggers on all holdings.
    Populates universal_data['analysis']['harvest_triggers_df'].
    """
    
def _check_triggers(row: pd.Series, snapshot: pd.DataFrame, etf: str) -> Tuple[str, float]:
    """
    Evaluate H1/H2/H3 conditions.
    Returns (trigger_name, base_trim_percent) or (None, 0.0).
    """
    
def _apply_sleeve_cap(harvest_df: pd.DataFrame, total_s2_value: float, 
                      cap_percent: float) -> pd.DataFrame:
    """Scale down trim amounts if total exceeds weekly harvest cap"""
```

---

### **decision_engine/generate_actions.py**

```python
"""
Combines budget, health, and harvest into final BUY/TRIM/NO_ACTION plan.
"""

def generate_weekly_actions(universal_data: Dict) -> Dict:
    """
    Main entry point - generates complete action plan.
    Populates universal_data['execution_plan']['weekly_actions_df'].
    """
    
def _filter_eligible_for_buy(health_df: pd.DataFrame, holdings: pd.DataFrame) -> list:
    """Return ETFs that pass health AND are underweight"""
    
def _prioritize_etfs(eligible: list, health_df: pd.DataFrame) -> list:
    """Sort by priority: lower ATR%, then higher RSI"""
    
def _allocate_budget(eligible: list, budget: float, holdings: pd.DataFrame,
                     snapshot: pd.DataFrame, configs: dict, universal_data: Dict) -> list:
    """Distribute budget across eligible ETFs proportionally"""
    
def _determine_no_action_reason(etf: str, health_df: pd.DataFrame, 
                                 holdings: pd.DataFrame) -> str:
    """Determine why an ETF has no action (for reporting)"""
```

---

### **decision_engine/format_outputs.py**

```python
"""
Transforms analysis results into sheet-ready DataFrames.
"""

def format_all_sheets(universal_data: Dict) -> Dict:
    """
    Main entry point - formats all output sheets.
    Populates universal_data['report_sheets'].
    """
    
def _format_dashboard(universal_data: Dict) -> pd.DataFrame:
    """Create summary metrics table"""
    
def _format_config(universal_data: Dict) -> pd.DataFrame:
    """Pass-through CONFIG sheet"""
    
def _format_portfolio(universal_data: Dict) -> pd.DataFrame:
    """Format holdings with projected post-action weights"""
    
def _format_signals(universal_data: Dict) -> pd.DataFrame:
    """Format technical indicators for SIGNALS sheet"""
    
def _format_actions(universal_data: Dict) -> pd.DataFrame:
    """Format weekly action plan"""
    
def _format_harvest_log(universal_data: Dict) -> pd.DataFrame:
    """Extract harvest actions for append-only log"""
    
def _format_logs(universal_data: Dict) -> pd.DataFrame:
    """Create system log entries for this run"""
```

---

### **live_update/trigger_monitor.py**

```python
"""
Continuously monitors Excel for UPDATE_TRIGGER flag.
Initiates pipeline execution when triggered.
"""

def monitor_excel_trigger(universal_data: Dict, poll_interval_seconds: int = 30) -> None:
    """
    Main monitoring loop - checks Excel every N seconds.
    Runs forever in daemon mode.
    """
    
def _read_trigger_status(universal_data: Dict) -> dict:
    """Read control cells from SYSTEM_CONTROL sheet"""
    
def _set_run_status(universal_data: Dict, status: str, error_msg: str = None) -> None:
    """Update RUN_STATUS and ERROR_MESSAGE in Excel"""
    
def _reset_trigger_flag(universal_data: Dict) -> None:
    """Set UPDATE_TRIGGER back to FALSE after completion"""
```

---

### **live_update/change_detector.py**

```python
"""
Detects what changed in Excel CONFIG since last run.
Compares current state vs cached state.
"""

def detect_changes(universal_data: Dict) -> dict:
    """
    Main entry point - identifies changes.
    Returns dict with boolean flags:
      - config_changed
      - etf_lineup_changed
      - portfolio_changed
      - force_full_refresh
    """
    
def _load_cached_state(universal_data: Dict) -> dict:
    """Load previous run's state from state_cache.json"""
    
def _capture_current_state(universal_data: Dict) -> dict:
    """Capture current Excel state for comparison"""
    
def _configs_differ(cached: dict, current: dict) -> bool:
    """Compare system parameters (budget, risk controls)"""
    
def _etf_lineup_differs(cached: pd.DataFrame, current: pd.DataFrame) -> bool:
    """Compare ETF lineup (added/removed/reweighted ETFs)"""
    
def _portfolio_differs(cached: pd.DataFrame, current: pd.DataFrame) -> bool:
    """Compare holdings (manual updates to units/prices)"""
    
def _save_state_cache(universal_data: Dict) -> None:
    """Save current state to cache for next run comparison"""
```

---

### **live_update/pipeline_orchestrator.py**

```python
"""
Decides which modules to re-run based on detected changes.
Executes minimal set of phases needed.
"""

def execute_incremental_update(universal_data: Dict) -> Dict:
    """
    Main entry point - smart re-execution engine.
    Only runs necessary modules based on change type.
    """
    
def _run_full_pipeline(universal_data: Dict) -> Dict:
    """Execute all phases (Phases 1-4)"""
    
def _run_data_pipeline(universal_data: Dict) -> Dict:
    """Execute Phase 2 only (market data sync)"""
    
def _run_decision_engine(universal_data: Dict) -> Dict:
    """Execute Phase 3 only (strategy calculations)"""
    
def _determine_required_phases(changes: dict) -> list:
    """
    Decision matrix:
    - config_changed → Phase 3
    - etf_lineup_changed → Phase 2 + 3
    - portfolio_changed → Phase 3
    - force_full_refresh → All phases
    """
```

---

### **live_update/status_manager.py**

```python
"""
Manages control cells in SYSTEM_CONTROL sheet.
"""

def update_control_cells(universal_data: Dict, updates: dict) -> None:
    """
    Update specific control cells in SYSTEM_CONTROL sheet.
    Example updates dict:
      {'UPDATE_TRIGGER': 'FALSE', 'RUN_STATUS': 'SUCCESS', 'LAST_RUN_DATE': '...'}
    """
    
def set_status_running(universal_data: Dict) -> None:
    """Mark pipeline as RUNNING (prevents double-execution)"""
    
def set_status_success(universal_data: Dict) -> None:
    """Mark pipeline as SUCCESS and reset trigger"""
    
def set_status_error(universal_data: Dict, error_msg: str) -> None:
    """Mark pipeline as ERROR with message"""
```

---

## 🔐 Security & Credentials Management

### Credentials Storage

```
configs/credentials.json (GITIGNORED)
├── upstox:
│   ├── API_KEY
│   ├── SECRET_KEY
│   ├── RURL
│   ├── TOTP_KEY
│   ├── MOBILE_NO
│   └── PIN
└── google_sheets:
    ├── type: "service_account"
    ├── project_id
    ├── private_key
    ├── client_email
    └── ...
```

### .gitignore Rules

```
# Credentials (NEVER commit)
configs/credentials.json
source/access_token.json
source/state_cache.json

# Data files (too large for git)
source/data/*.csv
source/data/*.parquet
source/etf_ohlcv_data/*.json

# Logs
logs/*.log

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp
```

---

## 🧪 Testing Strategy

### Unit Tests Structure

```
tests/
├── test_budget_calculator.py
├── test_health_checker.py
├── test_harvest_checker.py
├── test_action_generator.py
├── test_change_detector.py
└── fixtures/
    ├── mock_universal_data.json
    ├── mock_indicator_snapshot.csv
    └── mock_holdings.csv
```

### Example Test

```python
# tests/test_budget_calculator.py

import pytest
from decision_engine.calculate_budget import calculate_weekly_budget

def test_budget_calculation_underweight():
    """Test budget calculation when S2 is underweight target"""
    
    universal_data = load_fixture('mock_universal_data.json')
    universal_data['portfolio_state']['summary']['current_s2_weight_pct'] = 30.0
    
    result = calculate_weekly_budget(universal_data)
    
    assert result['analysis']['weekly_budget'] > 0
    assert result['analysis']['gap_to_target'] > 0

def test_budget_calculation_at_target():
    """Test budget is zero when at target weight"""
    
    universal_data = load_fixture('mock_universal_data.json')
    universal_data['portfolio_state']['summary']['current_s2_weight_pct'] = 34.0
    
    result = calculate_weekly_budget(universal_data)
    
    assert result['analysis']['weekly_budget'] == 0
```

---

## 📊 Performance Considerations

### Optimization Points

1. **OHLCV Download:**
   - Parallel fetching for multiple ETFs (use `concurrent.futures`)
   - Cache validation before download
   - Gzip compression for storage

2. **Indicator Calculation:**
   - Pre-compiled indicator library (pandas-ta is fast)
   - Only calculate for required timeframes
   - Parquet storage for fast retrieval

3. **Google Sheets I/O:**
   - Batch updates instead of cell-by-cell
   - Use `update_range()` for multiple cells
   - Cache credentials (avoid re-authentication)

4. **Change Detection:**
   - Hash-based comparison (faster than full DataFrame diff)
   - Store compressed state cache

### Expected Runtime

| Phase | Duration | Bottleneck |
|-------|----------|------------|
| Phase 1: Init | 1-2s | Google Sheets read |
| Phase 2: Data | 30-60s | Upstox API rate limits |
| Phase 3: Decision | 2-5s | Indicator calculations |
| Phase 4: Output | 3-5s | Google Sheets write |
| **Total** | **40-75s** | Network I/O |

---

## 🚨 Error Handling Strategy

### Error Categories

1. **Authentication Failures**
   - Retry with exponential backoff
   - Alert if 3 consecutive failures
   - Fallback: use cached token if within validity

2. **API Rate Limits**
   - Respect 429 responses
   - Implement adaptive delays
   - Log and continue for non-critical ETFs

3. **Data Quality Issues**
   - Skip corrupted OHLCV files
   - Log missing indicators
   - Continue with available data

4. **Configuration Errors**
   - Validate on load
   - Fail fast with clear error messages
   - Provide default values where safe

### Logging Levels

```python
INFO:     Normal operations (pipeline start, phase complete)
WARNING:  Recoverable issues (cache miss, single ETF failure)
ERROR:    Module failures (API timeout, file corruption)
CRITICAL: Pipeline halts (invalid config, auth total failure)
```

---

## 📈 Monitoring & Observability

### Key Metrics to Track

1. **Pipeline Health:**
   - Success rate (%)
   - Average runtime (seconds)
   - Failed module frequency

2. **Data Quality:**
   - ETFs with missing data
   - Indicator calculation failures
   - Stale cache warnings

3. **Trading Activity:**
   - Buy actions per week
   - Trim actions per week
   - Budget utilization (%)
   - Carry-forward accumulation

### Log Analysis Queries

```bash
# Count errors by module
grep "ERROR" logs/trading_system.log | grep -oP '\[.*?\]' | sort | uniq -c

# Find authentication issues
grep "AUTH.*FAILURE" logs/trading_system.log

# Track budget trends
grep "Weekly Budget" logs/trading_system.log | tail -10
```

---

## 🔄 Deployment Checklist

### Initial Setup

- [ ] Clone repository
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `configs/credentials.json.template` → `credentials.json`
- [ ] Fill in Upstox API credentials
- [ ] Fill in Google Sheets service account key
- [ ] Update `system_config.json`:
  - [ ] Set `google_sheets.spreadsheet_id`
  - [ ] Verify all URLs are accessible
- [ ] Create Google Sheet with required tabs:
  - [ ] SYSTEM_CONTROL
  - [ ] CONFIG
  - [ ] STATE
  - [ ] SIGNALS
  - [ ] WEEKLY_ACTIONS
  - [ ] HARVEST_LOG
  - [ ] DASHBOARD
  - [ ] LOGS
- [ ] Run first-time full sync: `python main.py --mode force_full_refresh`
- [ ] Verify all sheets populated correctly

### Production Deployment

- [ ] Set up systemd service (Linux) or Task Scheduler (Windows)
- [ ] Configure log rotation
- [ ] Set up monitoring alerts (email/SMS on CRITICAL errors)
- [ ] Document runbook for common failures
- [ ] Schedule weekly manual verification

---

## 📚 Dependencies (`requirements.txt`)

```
# Core
pandas==2.1.3
numpy==1.26.2

# Technical Indicators
pandas-ta==0.3.14b

# Data Fetching
requests==2.31.0
pyotp==2.9.0

```
# Browser Automation
playwright==1.40.0

# Google Sheets Integration
gspread==5.12.0
oauth2client==4.1.3

# Date/Time Handling
pytz==2023.3

# Data Storage
pyarrow==14.0.1  # For parquet file support

# Logging & Utilities
tqdm==4.66.1

# Testing (optional)
pytest==7.4.3
pytest-cov==4.1.0

# Type Hints (optional)
typing-extensions==4.8.0
```

### Installation Command

```bash
pip install -r requirements.txt

# Post-install: Initialize Playwright browsers
playwright install chromium
```

---

## 🎯 Phase 5 Execution Logic (Detailed Decision Matrix)

### Change Detection Rules

```python
# live_update/change_detector.py

CHANGE_DETECTION_RULES = {
    "config_changed": {
        "monitored_params": [
            "S2_Target_%",
            "Weeks_to_Glide",
            "Weekly_Transfer_Cap_%",
            "S2_Weekly_Budget_Cap_%",
            "DriftBand_%",
            "CoreFloor_%",
            "ATR_Ceiling_%",
            "Single_ETF_Max_%",
            "MaxTrimPerETF_%",
            "WeeklyHarvestCap_%"
        ],
        "action": "rerun_decision_engine"
    },
    
    "etf_lineup_changed": {
        "monitored_fields": [
            "ETF added/removed",
            "Enabled flag changed",
            "Target_% modified",
            "ATR_Override_% changed"
        ],
        "action": "rerun_data_pipeline_and_decision_engine"
    },
    
    "portfolio_changed": {
        "monitored_fields": [
            "Units modified",
            "Avg_Buy_Price updated",
            "Manual holdings adjustment"
        ],
        "action": "rerun_decision_engine"
    }
}
```

### Execution Decision Tree

```
┌──────────────────────────────────────────────────────────┐
│         UPDATE_TRIGGER = TRUE detected                   │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│   Check FORCE_FULL_REFRESH flag                          │
└──────────────────────────────────────────────────────────┘
                │                    │
                │ TRUE               │ FALSE
                ▼                    ▼
    ┌───────────────────┐   ┌────────────────────────┐
    │ Run ALL Phases    │   │ Load state_cache.json  │
    │ (1-4)             │   │ Compare with current   │
    └───────────────────┘   └────────────────────────┘
                                        │
                                        ▼
        ┌───────────────────────────────────────────────┐
        │  What changed?                                │
        └───────────────────────────────────────────────┘
                │              │              │
       ┌────────┴────────┐    │    ┌────────┴──────────┐
       │                 │    │    │                   │
       ▼                 ▼    ▼    ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Config Changed│  │Lineup Changed│  │Portfolio     │
│              │  │              │  │Changed       │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                  │
       ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Skip Phase 2  │  │Run Phase 2   │  │Skip Phase 2  │
│Run Phase 3   │  │Run Phase 3   │  │Run Phase 3   │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                  │
       └─────────────────┴──────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │  Always Run Phase 4      │
            │  (Write to Excel)        │
            └──────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │  Update Control Cells:   │
            │  - UPDATE_TRIGGER→FALSE  │
            │  - RUN_STATUS→SUCCESS    │
            │  - LAST_RUN_DATE→now     │
            └──────────────────────────┘
                          │
                          ▼
            ┌──────────────────────────┐
            │  Save new state cache    │
            └──────────────────────────┘
```

---

## 🔧 Advanced Configuration Options

### Debug Mode Configuration

```json
// configs/system_config.json

{
  "debug_controls": {
    "force_fresh_login": false,
    "force_nse_refresh": false,
    "force_upstox_refresh": false,
    "force_ohlcv_resync": false,
    "force_indicator_recalc": false,
    
    "enable_playwright_headless": true,
    "playwright_timeout_seconds": 60,
    "save_raw_api_responses": true,
    "mock_mode": false,
    
    "log_api_requests": true,
    "log_cache_hits_misses": true,
    "verbose_indicator_calc": false,
    
    "dry_run_mode": false,  // Calculate but don't write to Excel
    "skip_excel_write": false,
    "simulate_failures": false  // For testing error handling
  }
}
```

### Performance Tuning

```json
// configs/system_config.json

{
  "performance": {
    "enable_parallel_etf_fetch": true,
    "max_parallel_workers": 4,
    "ohlcv_fetch_timeout_seconds": 30,
    "indicator_calc_chunk_size": 1000,
    "cache_compression": "gzip",
    "use_fast_parquet_writer": true
  }
}
```

### Retry & Resilience

```json
// configs/system_config.json

{
  "resilience": {
    "api_max_retries": 3,
    "api_retry_delay_seconds": 5,
    "api_exponential_backoff": true,
    "api_timeout_seconds": 30,
    
    "continue_on_single_etf_failure": true,
    "abort_on_critical_module_failure": true,
    
    "auto_recover_from_cache_corruption": true,
    "fallback_to_previous_state_on_error": false
  }
}
```

---

## 📊 Excel Sheet Templates

### SYSTEM_CONTROL Sheet Layout

```
     A                    B                     C
1  | Parameter         | Value               | Last_Updated
2  | UPDATE_TRIGGER    | FALSE               | 2024-11-20 10:30:00
3  | FORCE_FULL_REFRESH| FALSE               | -
4  | RUN_STATUS        | SUCCESS             | 2024-11-20 10:35:00
5  | ERROR_MESSAGE     | -                   | -
6  | LAST_RUN_DATE     | 2024-11-20 10:35:00 | -
7  | PIPELINE_VERSION  | 2.0                 | -
8  | EXECUTION_MODE    | daemon              | -
```

**Client Instructions:**
1. Modify any CONFIG parameters
2. Set cell B2 (UPDATE_TRIGGER) to TRUE
3. Save file
4. Wait 30-60 seconds
5. Refresh sheets to see updated results
6. B2 will auto-reset to FALSE

---

### CONFIG Sheet Layout

```
SECTION A: SYSTEM PARAMETERS
─────────────────────────────────────────────────────────────
Parameter                 | Value  | Unit    | Description
──────────────────────────────────────────────────────────────
S2_Target_%               | 34.0   | %       | Target allocation
Weeks_to_Glide            | 52     | weeks   | Spread gap over weeks
Enable_Carry_Forward      | TRUE   | boolean | Carry unused budget
Weekly_Transfer_Cap_%     | 5.0    | %       | Max % to transfer weekly
S2_Weekly_Budget_Cap_%    | 1.25   | %       | Max % of S2 to deploy


SECTION B: RISK CONTROLS
─────────────────────────────────────────────────────────────
Parameter                 | Value  | Unit    | Description
──────────────────────────────────────────────────────────────
DriftBand_%               | 10.0   | %       | Tolerance before action
CoreFloor_%               | 70.0   | %       | Min % of target
ATR_Ceiling_%             | 2.0    | %       | Default volatility limit
Single_ETF_Max_%          | 35.0   | %       | Max single position
MaxTrimPerETF_%           | 25.0   | %       | Max trim per harvest
WeeklyHarvestCap_%        | 12.0   | %       | Max weekly profit taking


SECTION C: ETF LINEUP
─────────────────────────────────────────────────────────────
ETF_ID | Ticker      | Enabled | Target_% | ATR_Override_% | Tags
────────────────────────────────────────────────────────────────
ETF_01 | NIFTYBEES   | TRUE    | 40.0     | -              | Core,Broad
ETF_02 | BANKBEES    | TRUE    | 20.0     | 2.5            | Core,Financials
ETF_03 | GOLDBEES    | TRUE    | 15.0     | 3.0            | Satellite,Commodity
ETF_04 | JUNIORBEES  | TRUE    | 10.0     | -              | Satellite,Midcap
ETF_05 | ITBEES      | TRUE    | 6.0      | 2.8            | Satellite,Sector
ETF_06 | SILVERBEES  | TRUE    | 6.0      | 3.5            | Satellite,Commodity
ETF_07 | MON100      | FALSE   | 3.0      | -              | Satellite
                                    ↑
                            Must sum to 100%
```

---

## 🎨 User Workflows

### Workflow 1: Change Budget Allocation

```
Step 1: Open Google Sheet
Step 2: Navigate to CONFIG tab
Step 3: Modify S2_Target_% (e.g., 34.0 → 36.0)
Step 4: Set UPDATE_TRIGGER = TRUE
Step 5: Save
Step 6: Wait 30-60 seconds
Step 7: Check DASHBOARD tab for new budget
Step 8: Check WEEKLY_ACTIONS tab for updated trades
```

**System Response:**
- Detects config change
- Skips Phase 2 (data unchanged)
- Re-runs Phase 3 (budget, health, harvest, actions)
- Updates all output sheets
- Resets trigger

---

### Workflow 2: Add New ETF

```
Step 1: Open CONFIG tab
Step 2: Add new row in ETF Lineup section:
        ETF_08 | CPSEETF | TRUE | 3.0 | - | Satellite
Step 3: Adjust other Target_% so sum = 100%
Step 4: Set UPDATE_TRIGGER = TRUE
Step 5: Save
Step 6: Wait 2-3 minutes (data fetch required)
Step 7: Verify CPSEETF appears in STATE and SIGNALS tabs
```

**System Response:**
- Detects ETF lineup change
- Re-runs Phase 2 (fetches CPSEETF data)
- Re-runs Phase 3 (includes CPSEETF in decisions)
- Updates all sheets

---

### Workflow 3: Manual Portfolio Correction

```
Step 1: Open STATE tab
Step 2: Manually update Units or Avg_Buy_Price
        (e.g., broker executed different price)
Step 3: Navigate to CONFIG → SYSTEM_CONTROL
Step 4: Set UPDATE_TRIGGER = TRUE
Step 5: Save
Step 6: Wait 30-60 seconds
Step 7: Check WEEKLY_ACTIONS for recalculated plan
```

**System Response:**
- Detects portfolio change
- Skips Phase 2 (market data unchanged)
- Re-runs Phase 3 (recalculates gaps, actions)
- Updates output sheets

---

## 🛠️ Maintenance & Operations

### Daily Operations

```bash
# Check daemon status
systemctl status s2-trading

# View recent logs
tail -f logs/trading_system.log

# Check last successful run
grep "PIPELINE EXECUTION COMPLETE" logs/trading_system.log | tail -1

# View today's actions
grep "WEEKLY_ACTIONS" logs/trading_system.log | grep $(date +%Y-%m-%d)
```

### Weekly Tasks

- [ ] Review WEEKLY_ACTIONS sheet
- [ ] Execute planned trades in broker
- [ ] Update STATE sheet with actual fills
- [ ] Verify HARVEST_LOG for trim history
- [ ] Check ERROR_MESSAGE cell for issues

### Monthly Tasks

- [ ] Analyze performance trends (DASHBOARD)
- [ ] Review log file size (rotate if >100MB)
- [ ] Verify cache file integrity
- [ ] Update strategy_config.json if needed
- [ ] Backup state_cache.json

---

## 🔍 Troubleshooting Guide

### Issue: Pipeline Not Triggering

**Symptoms:** UPDATE_TRIGGER = TRUE but nothing happens

**Diagnosis:**
```bash
# Check if daemon is running
ps aux | grep main.py

# Check logs for errors
grep "ERROR\|CRITICAL" logs/trading_system.log | tail -20

# Verify Google Sheets connection
python -c "from connectors.sheets_reader import _authenticate_gspread; print('OK')"
```

**Solutions:**
1. Restart daemon: `systemctl restart s2-trading`
2. Check credentials.json validity
3. Verify Google Sheets API quota not exceeded

---

### Issue: Authentication Failures

**Symptoms:** "Failed to authenticate with Upstox"

**Diagnosis:**
```bash
# Check token cache
cat source/access_token.json

# Check if past 3:30 AM IST expiry
python -c "from data_pipeline.upstox_auth import _is_token_expired; print(_is_token_expired())"
```

**Solutions:**
1. Set `force_fresh_login: true` in system_config.json
2. Verify Upstox credentials in credentials.json
3. Check TOTP_KEY is correct
4. Manually delete access_token.json to force re-auth

---

### Issue: Missing Indicator Data

**Symptoms:** Health checks all failing, indicator_snapshot_df empty

**Diagnosis:**
```bash
# Check OHLCV files exist
ls -lh source/etf_ohlcv_data/

# Check indicator parquet
ls -lh source/data/indicator_data.parquet

# Check logs
grep "INDICATOR" logs/trading_system.log | grep "ERROR"
```

**Solutions:**
1. Set `force_ohlcv_resync: true` to re-download data
2. Set `force_indicator_recalc: true` to recalculate
3. Verify pandas-ta library installed correctly
4. Check ETF symbols are valid NSE tickers

---

### Issue: Excel Sheets Not Updating

**Symptoms:** Pipeline completes but sheets unchanged

**Diagnosis:**
```bash
# Check Phase 4 logs
grep "PHASE_4" logs/trading_system.log | tail -20

# Test Google Sheets write access
python -c "from connectors.sheets_writer import GoogleSheetsWriter; print('OK')"
```

**Solutions:**
1. Verify service account has Editor access to sheet
2. Check spreadsheet_id in system_config.json is correct
3. Verify sheet tab names match exactly (case-sensitive)
4. Check Google Sheets API quota

---

## 📈 Performance Benchmarks

### Expected Execution Times (Reference Machine: 4-core, 16GB RAM)

| Operation | Duration | Notes |
|-----------|----------|-------|
| Initialize + Load Config | 1-2s | Network dependent |
| Upstox Authentication (cached) | <1s | Token from cache |
| Upstox Authentication (fresh) | 15-25s | Browser automation |
| Instrument Master Fetch | 3-5s | Compressed download |
| OHLCV Sync (1 ETF, incremental) | 2-4s | 1-2 API calls |
| OHLCV Sync (6 ETFs, incremental) | 15-30s | Rate limited |
| Indicator Calculation (6 ETFs) | 3-5s | pandas-ta efficient |
| Decision Engine (all modules) | 2-3s | Pure computation |
| Write to Google Sheets | 4-6s | 7 sheets, network |
| **Total (incremental run)** | **30-60s** | Typical weekly |
| **Total (full refresh)** | **60-120s** | All data re-fetched |

---

## 🎓 Glossary

### Key Terms

**Universal Data:** Central in-memory dictionary that flows through all modules, containing configs, market data, analysis results, and execution plan.

**Health Score:** 0-4 rating based on passing technical conditions (TSI, RSI, VWMA slope, ATR). Only score=4 allows buying.

**Harvest Triggers:** Conditions (H1/H2/H3) that signal profit-taking opportunities (RSI stretch, volatility spike, trend breakdown).

**Drift Band:** Tolerance range (±%) around target allocation before action is required.

**Core Floor:** Minimum percentage of target allocation an ETF must maintain (prevents over-trimming).

**Glide Path:** Gradual approach to target allocation spread over N weeks (avoids large single deployments).

**Carry Forward:** Unused weekly budget accumulated for next week (enables larger buys when opportunities align).

**GTT Price:** Good-Till-Triggered order price calculated as: Friday_Close - (0.5 × ATR).

**Indicator Snapshot:** Latest technical indicator values per ETF (one row per ETF-timeframe).

**State Cache:** JSON file storing previous Excel state for change detection.

---

## 📦 Deliverables Summary

### What Gets Created

1. **Source Code:**
   - 25+ Python modules across 5 directories
   - 3 JSON configuration files
   - requirements.txt

2. **Data Files:**
   - etf_instrument_master.csv (ETF list)
   - {SYMBOL}_1m_history.json (price data per ETF)
   - indicator_data.parquet (full indicator history)
   - access_token.json (cached token)
   - state_cache.json (change detection)

3. **Google Sheets:**
   - 8 tabs: SYSTEM_CONTROL, CONFIG, STATE, SIGNALS, WEEKLY_ACTIONS, HARVEST_LOG, DASHBOARD, LOGS
   - Auto-updating based on trigger flag

4. **Documentation:**
   - This modular design document
   - Inline code comments
   - Troubleshooting runbook

---

## 🚀 Quick Start Commands

```bash
# Initial setup
git clone <repo>
cd S2_Trading_System
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

pip install -r requirements.txt
playwright install chromium

# Configure
cp configs/credentials.json.template configs/credentials.json
# Edit credentials.json with your API keys
# Edit configs/system_config.json with Sheet ID

# First run (full sync)
python main.py --mode force_full_refresh

# Production daemon mode
python main.py --mode daemon

# OR scheduled mode (cron/Task Scheduler)
python main.py --mode single_run
```

---

## 📋 Final Checklist

### Before Going Live

- [ ] All credentials configured correctly
- [ ] Google Sheet created with all 8 tabs
- [ ] Service account has Editor access
- [ ] First full sync completed successfully
- [ ] All sheets populated with data
- [ ] Daemon mode tested locally
- [ ] Error handling tested (invalid credentials, missing data)
- [ ] Change detection tested (modify CONFIG, verify re-run)
- [ ] Manual portfolio update tested
- [ ] Add new ETF workflow tested
- [ ] Logs rotating correctly
- [ ] Monitoring alerts configured
- [ ] Backup strategy in place

---
