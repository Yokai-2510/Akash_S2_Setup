## **Sheet 1: CONFIG - Parameters Table**

|Column|Meaning|
|---|---|
|**Parameter**|Name of the configuration setting (e.g., `Weeks_to_Glide`)|
|**Value**|The actual number/boolean for that parameter (e.g., `52`)|
|**Unit**|What the value represents (weeks, %, boolean, etc.)|
|**Description**|Human-readable explanation of what the parameter controls|

## **Sheet 1: CONFIG - ETF Lineup Table**

|Column|Meaning|
|---|---|
|**ETF_ID**|Unique identifier for the ETF (ETF_01, ETF_02, etc.) - used to link across sheets|
|**Ticker**|Exchange symbol (e.g., NIFTYBEES, JUNIORBEES)|
|**Enabled**|TRUE = include in strategy, FALSE = skip this slot|
|**Target_%**|What % of S2 portfolio this ETF should be (all enabled ETFs must sum to 100%)|
|**ATR_Override_%**|Custom volatility ceiling for this ETF (overrides the default 2.0% if specified)|
|**Tags**|Comma-separated labels for sector caps (e.g., "Core,Broad" or "Satellite,Financials")|
|**Notes**|Free-text field for human reference (e.g., "Large-cap broad index")|

---

## **Sheet 2: STATE (Portfolio Snapshot)**

|Column|Meaning|
|---|---|
|**ETF_ID**|Links to CONFIG table (ETF_01, ETF_02, etc.)|
|**Ticker**|Symbol for quick reference|
|**Units**|How many units/shares currently held|
|**Avg_Cost**|Average purchase price per unit (cost basis)|
|**Current_Price**|Latest market price (from this week's close)|
|**Market_Value**|Units × Current_Price (current rupee value of holding)|
|**Current_%**|(Market_Value ÷ Total_S2_Value) × 100 (actual weight in portfolio)|
|**Target_%**|Desired weight from CONFIG (what we're aiming for)|
|**Gap_%**|Current_% - Target_% (positive = overweight, negative = underweight)|
|**Status**|UNDER / NEAR / OVER based on Gap_% vs DriftBand (see logic below)|

**Status Logic:**

- **UNDER**: `Current_% < (Target_% - DriftBand_%)` → Need to buy
- **NEAR**: Within DriftBand range → No action needed
- **OVER**: `Current_% > (Target_% + DriftBand_%)` → May trim if triggers fire

---

## **Sheet 3: WEEKLY_ACTIONS (Audit Log)**

|Column|Meaning|
|---|---|
|**Week_Date**|Monday date of the trading week (e.g., 2024-01-08)|
|**ETF_ID**|Which ETF this action applies to|
|**Action**|BUY / TRIM / NO_ACTION|
|**Units**|Number of units bought or sold|
|**Price**|Execution price (GTT fill price for buys, close price for trims)|
|**Amount**|Units × Price (rupee value of transaction)|
|**Reason**|Why this action was taken (see Reason Codes below)|
|**Pre_%**|ETF weight BEFORE this action|
|**Post_%**|ETF weight AFTER this action|
|**Trigger**|Which harvest trigger fired (for trims): H1_Stretch / H2_VolSpike / H3_Breakdown, or "-" for buys|
|**Status**|FILLED / CARRY_FWD / SKIPPED|

**Reason Codes:**

- `UNDER+H4` = Underweight ETF + Health Score = 4 → Full slice buy
- `UNDER+H3` = Underweight ETF + Health Score = 3 → Half slice buy
- `H1_Stretch` = RSI > 70 or price > 13W high → Trim 10%
- `H2_VolSpike` = ATR% jumped > 35% or > 80th percentile → Trim 15%
- `H3_Breakdown` = TSI crossed down or price < 50DMA → Trim 15-25%
- `ALL_ETF_FAIL_HEALTH` = No ETFs passed health checks → Carry budget forward
- `CARRY_FORWARD` = Budget not spent, added to Accrued_S2_Carry

**Trigger Details (for Trims):**

- `RSI>70` = RSI exceeded 70
- `ATR%>2.8` = ATR% breached the ceiling
- `TSI_Cross` = TSI crossed below its Signal line
- `<50DMA` = Price fell below 50-day moving average

---

## **Sheet 4: SIGNALS (Technical Indicators)**

|Column|Meaning|
|---|---|
|**Week_Date**|Monday date of the trading week|
|**ETF_ID**|Which ETF these signals apply to|
|**TSI**|True Strength Index (25,13) - measures trend momentum (-100 to +100)|
|**TSI_Signal**|EMA(7) of TSI - smoothed reference line for crossovers|
|**RSI**|Relative Strength Index (14) - momentum oscillator (0 to 100)|
|**VWMA_Slope**|Volume-Weighted Moving Average (20) slope (current vs 1 week ago)|
|**ATR%**|Average True Range as % of close (volatility measure)|
|**vs_50DMA**|How far price is from 50-day moving average (e.g., +2.5% means 2.5% above)|
|**vs_13W_High**|Distance from 13-week rolling high (e.g., -1.2% means 1.2% below the high)|
|**Health**|Health Score (0-4) - counts how many health conditions passed|
|**Pass**|TRUE if Health = 4 (all conditions met), FALSE otherwise|

**Health Score Breakdown (each adds +1):**

1. ✅ TSI > TSI_Signal (trend is up)
2. ✅ RSI > 50 (momentum is positive)
3. ✅ VWMA_Slope ≥ 0 (volume-weighted price trending up)
4. ✅ ATR% ≤ ATR_Ceiling_% (volatility is manageable)

**Pass = TRUE only if all 4 conditions met (Health = 4)**

---
