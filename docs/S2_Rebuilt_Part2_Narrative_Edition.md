**S2 — ETF Backbone (Flexible)\
Part 2: Profit‑Only Harvesting, Defensive & Guardrails (Narrative Edition)**

*Trim small, trim green, and protect the core — clear signals, simple sizing, steady behavior*

## **1) Purpose & Principles — Why We Harvest**
Harvesting is not market timing. It is a small, rules‑based way to realize gains when price action becomes stretched or risk flares, without disrupting the long‑term compounding engine. We only trim when the position is in profit, and we never over‑trim. Proceeds go to Defensive and re‑enter later via normal Monday SIPs when health improves.

This keeps the system emotionally calm: we do not chase, we do not panic. We simply lighten up a little when the tape says “hot” or “fragile,” and we stay invested otherwise.
## **2) Eligibility — The Two Gates**
Harvesting happens only if BOTH are true at the weekly close:\
• The ETF position is in profit (average buy < current price).\
• One of the harvest triggers (H1/H2/H3) fires.
## **3) Signals & Triggers — What to Look For (Weekly)**
H1 — Stretch (price extended):

• RSI(14) > 70 OR weekly close > prior 13‑week high by a cushion (e.g., >1×ATR).\
• Distance from 20‑DMA unusually large (e.g., >2×ATR above 20‑DMA).\
• Optional: Bollinger Band upper tag with follow‑through.\
Rationale: take a small slice when momentum is euphoric; let the rest run.

H2 — Volatility Spike (fragile tape):

• ATR% jumps above its rolling 6‑month 80th percentile, or week‑to‑week ATR% change > 35%.\
• Wide‑range weekly candles with long upper wicks.\
• Gap‑up that fades (open near high, close back in range) after an extended run.\
Rationale: elevated variance increases drawdown risk; a modest trim reduces tail exposure.

H3 — Health Breakdown (first deterioration):

• TSI(25,13) crosses below its Signal (EMA(7) of TSI).\
• AND/OR weekly close < 50‑DMA (first break after an uptrend).\
• Optional confirmation: VWMA(20) slope turns negative.\
Rationale: trend momentum is rolling over; realize part of the gain without abandoning the sleeve.
### **Best‑Practice Tips (Signals)**
• Use weekly data to avoid noise. Do not react intraday.\
• Treat triggers as binary — either on or off. No “half‑credit.”\
• Prefer “first occurrence” after an advance for H3; avoid repeated trims on the same minor chop.\
• If multiple triggers fire, pick the strongest sizing rule below but still respect caps and floors.
## **4) Sizing the Trim — Small, Variable, Capped**
Base trim sizes (percent of units):\
• H1 — Stretch: 10%\
• H2 — Vol Spike: 15%\
• H3 — Health Breakdown: 15% (up to 25% if BOTH TSI crosses down AND weekly close < 50‑DMA)\
Per‑ETF weekly ceiling: MaxTrimPerETF% = 25% (hard cap — never exceed).\
Sleeve weekly ceiling: WeeklyHarvestCap% = 12% of S2 notional (sum of all ETF trims). If proposed trims exceed the sleeve cap, scale all ETF trims down proportionally.
### **Why these numbers?**
10–15% is large enough to matter but small enough to keep the core compounding. The 25% hard cap protects against accidental de‑risking in a single week. The sleeve cap limits overall churn and preserves the S2 backbone.
## **5) Floors & Protection — Guard the Core**
After trimming, two simple floors must hold:\
• Floor 1 (Drift Floor): Position ≥ (Target − DriftBand). If your trim would push below this, reduce the trim to stay above the floor.\
• Floor 2 (Core Floor): Position ≥ CoreFloor% × Target (e.g., 70%). Never let any ETF fall below this structural minimum.\
These floors ensure harvesting never hollows out core exposure or forces you to rebuild from scratch.
## **6) Routing & Redeploy — No Flip‑Flops**
Trim proceeds flow to Defensive (cash/metals), not back into S2 the same week. We do not net within the week and we do not re‑add tactically. Fresh buying happens only via Monday SIP when instruments pass health checks again. The allocator and the Gap ÷ Weeks\_to\_Glide method will naturally drip capital back toward targets over time.
## **7) Examples — Putting It Together**
Example A — Stretch Trim (H1):

• Large‑cap broad ETF is +18% from the last swing low; RSI(14) hits 73; price closes > 13‑week high by ~1.2×ATR.\
• Position is in profit → qualify. Apply H1 base trim = 10% of units.\
• Check floors: Target 20%, DriftBand ±10% → floor is 18%. If post‑trim weight stays ≥ 18%, proceed; if not, scale down.

Example B — Vol Spike (H2):

• Mid‑cap ETF shows weekly ATR% jumping from 1.7% to 2.5% (+47%), long upper wick, net small gain.\
• Position in profit → qualify. Apply H2 base trim = 15% of units. Respect sleeve cap (12% of S2) via proportional scaling if needed.

Example C — Breakdown (H3):

• Quality factor ETF sees TSI cross down and weekly close slips under 50‑DMA.\
• Position in profit → qualify. Apply H3 base trim = 15%; if both conditions hold (TSI↓ AND <50‑DMA), allow up to 25%, but never exceed caps/floors.
## **8) Cadence & Hygiene — How Often, How to Log**
• Cadence: Max 2 harvests per ETF in any rolling 4 weeks (cooldown). Avoid “chopping wood” in sideways markets.\
• Logging (per ETF/week): trigger (H1/H2/H3), signals snapshot (RSI, TSI/Signal, 50‑DMA status, ATR%), units trimmed, % of sleeve trimmed, post‑trade weight, floors/caps applied. Clear logs make audits and improvements easy.
## **9) Defaults & Owner Knobs (Implemented by Designer)**
• BaseTrim%: H1=10%, H2=15%, H3=15% (→25% if TSI↓ and <50‑DMA)\
• MaxTrimPerETF%: 25%\
• WeeklyHarvestCap%: 12% of S2\
• DriftBand: e.g., ±10% of target\
• CoreFloor%: 70% of target\
• Cooldown: max 2 harvests per ETF in any rolling 4 weeks
## **10) Context — Where This Fits**
Part 1 explains how the Asset Allocator provides the budget and how S2 buys healthy ETFs using Gap ÷ Weeks\_to\_Glide. Part 2 (this file) explains how we harvest profits without disrupting the core. Part 3 will outline the Monday Mix ritual, governance standards, and the single summary table the sheet designer will implement.
