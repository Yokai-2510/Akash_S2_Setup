
---
## 🎯 The Ultimate Goal (one-liner)

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
