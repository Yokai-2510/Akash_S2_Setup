**S2 — ETF Backbone (Flexible)\
Part 3: Monday Mix, Governance & Designer Summary (Narrative Edition)**

*One calm weekly ritual. Allocator-led budget. Health-first deployment. Clear logs. Zero drama.*

## **1) Purpose — What Monday Mix Is For**
Monday Mix is the weekly ritual that converts the allocator’s guidance into simple, auditable actions. The allocator has already embedded macro into S2 targets; Monday Mix uses that destination to compute a calm weekly budget, checks instrument health, and places GTT orders. If nothing qualifies, we spend nothing and try again next week. No ad hoc moves midweek; the power is in consistency.
## **2) The Weekly Sequence — Five Steps (with Best Practices)**
Step 1 — Read the Allocator & Compute Budget

• Pull Gap\_to\_Target\_S2 (difference between current S2 weight and allocator target).\
• Compute Weekly\_S2\_Base\_Budget = Gap\_to\_Target\_S2 ÷ Weeks\_to\_Glide (default 52).\
• Compute Weekly\_S2\_Capacity = min( Base\_Budget, Weekly\_Transfer\_Cap\_%×Total, S2\_Weekly\_Budget\_Cap\_%×Total ).\
• Optional Carry\_Forward: add Accrued\_S2\_Carry (unspent base) within the same caps.\
Best practice: keep Weeks\_to\_Glide stable; avoid tinkering unless regime changes materially.

Step 2 — Health Check (Micro-Only; S2 is Always-On)

• For each ETF: require TSI(25,13) > EMA(7) of TSI; RSI(14) > 50; VWMA(20) slope ≥ 0; ATR% ≤ ceiling (ETF overrides allowed).\
• Skip any ETF that fails. Do not override.\
Best practice: treat signals as binary; weekly timeframe only; no intraday/“almost”.

Step 3 — Pacing & Priority (Turn Budget into ETF Actions)

• Focus first on UNDERweight ETFs that pass health.\
• Health=4 → full slice; Health=3 → half slice; NEAR/OVER → no buy.\
• Tie-breaker (choose one and keep consistent): lower ATR% (less noise) or higher RSI (more momentum).\
• Enforce Single-ETF Max and Tag/Sector Caps from the lineup.\
Best practice: If nothing qualifies, do not force buys. Let budget carry forward.

Step 4 — Orders (GTT Placement)

• Default: one GTT per ETF at ~0.5×ATR below Friday close.\
• Optional 2-ladder only if Health=4 and ETF is materially UNDERweight (second step another 0.5×ATR lower).\
• One action per ETF per week; GTTs expire Friday close.\
Best practice: keep ladders rare; avoid over-engineering execution.

Step 5 — Log & Review (Audit Trail)

• Log: Weekly\_S2\_Capacity, ETFs acted on, units/₹ per ETF, pre/post weights, and any floors/caps that scaled actions.\
• For trims (from Part 2), record trigger (H1/H2/H3), signals snapshot (RSI, TSI/Signal, 50-DMA, ATR%), and % trimmed.\
• Review: Are we respecting floors (Target−DriftBand & CoreFloor%×Target), sleeve caps, and cooldowns?
## **3) Governance — Behaviors We Enforce**
• One weekly cycle; no intraday overrides; no discretionary averaging down.\
• No same-week netting of harvest proceeds into S2; redeploy only via Monday SIP.\
• Respect allocator caps and ETF lineup caps every week.\
• Keep the system auditable: simple rules, clear logs, minimal knobs.
## **4) Examples — Monday Mix in Action**
Example 1 — Calm Buy Week

• Gap\_to\_Target\_S2 = 5% of total; Weeks\_to\_Glide = 52 → Base\_Budget ≈ 0.096% of total.\
• Caps: Weekly\_Transfer\_Cap\_% = 5%; S2\_Weekly\_Budget\_Cap\_% = 1.25% → Weekly\_S2\_Capacity = 0.096%.\
• Health passing: Large-Cap Broad (UNDER & H=4), Quality (UNDER & H=3), Low-Vol (NEAR).\
• Actions: Full slice to Large-Cap Broad, half slice to Quality; no buy for Low-Vol.\
• Orders: GTTs at 0.5×ATR below Friday close; log details.

Example 2 — Nothing Qualifies (Carry-Forward Week)

• Budget computed as usual, but all candidates fail health (RSI<50 or VWMA slope<0).\
• Action: Spend = 0; add base budget to Accrued\_S2\_Carry; log reason codes.\
• Next week: budget = min(caps, base + accrued) — still health-first.
## **5) Designer Summary — Fields, Indicators & Knobs (Single Page)**

|Category|Field / Indicator|Meaning / Use|Default / Range|Where Used|
| :- | :- | :- | :- | :- |
|Allocator Link|Gap\_to\_Target\_S2(₹)|Needed to reach allocator target|From allocator|Budget Step 1|
|Allocator Link|Weeks\_to\_Glide|Weeks to spread the gap|52 (26–78)|Budget Step 1|
|Allocator Link|Weekly\_Transfer\_Cap\_%|Max total capital move/week|5% (allocator)|Budget Step 1|
|Allocator Link|S2\_Weekly\_Budget\_Cap\_%|Hard sleeve cap/week|1\.0–1.5%|Budget Step 1|
|Allocator Link|Accrued\_S2\_Carry|Unspent base budget (optional)|ON/OFF|Budget Step 1|
|Health|TSI(25,13)|Trend momentum|Weekly|Step 2|
|Health|Signal = EMA(7) of TSI|TSI smoothing for crosses|Weekly|Step 2|
|Health|RSI(14)|Momentum filter|>50|Step 2|
|Health|VWMA(20) slope|Volume-weighted trend check|≥0|Step 2|
|Health|ATR%|Volatility guard|≤2.0% (2.5–3.0% per ETF)|Step 2|
|Pacing|DriftBand|Allowed deviation around target|±10%|Floors & Step 3|
|Pacing|CoreFloor%|Structural minimum vs target|70% (example)|Floors & Step 3|
|Execution|GTT\_Pullback\_ATR|Buy offset from Friday close|0\.5×ATR (ladder opt.)|Step 4|
|Execution|Single-ETF Max|Max weight any ETF may hold|e.g., 35% of S2|Step 3/4|
|Execution|Tag/Sector Caps|Max exposure by tags|e.g., Financials ≤25%|Step 3/4|
|Harvest (from P2)|BaseTrim%|H1=10%, H2=15%, H3=15%→25%|Per Part 2|Logs (Step 5)|
|Harvest (from P2)|MaxTrimPerETF%|Per-ETF weekly max trim|25%|Governance|
|Harvest (from P2)|WeeklyHarvestCap%|Sleeve-level trim cap|12% of S2|Governance|
|Hygiene|Cooldown|Max harvests per ETF / 4 wks|2|Governance|
|Logging|Weekly Log Fields|Budget, signals, actions, reasons|Fixed schema|Step 5|
## **6) Minimal Implementation Notes (For the Sheet Designer)**
• Use booleans and min/max math; keep branches minimal.\
• Expose only primary knobs to owner; keep defaults sane.\
• The pipeline is linear: allocator budget → health filters → pacing & caps → orders → logs. When no buys qualify, carry forward budget (if enabled) and try next week.
