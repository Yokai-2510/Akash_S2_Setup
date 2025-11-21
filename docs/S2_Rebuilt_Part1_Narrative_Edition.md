**S2 — ETF Backbone (Flexible)\
Part 1: Philosophy, Allocator Link, ETF Lineup & Weekly Entry (Narrative Edition)**

*Always-on core, allocator-led budget (Gap ÷ Weeks\_to\_Glide), simple weekly actions — with practical guidance and examples*

## **1) Philosophy — What S2 Is (and Isn’t)**
S2 is the portfolio’s always-on equity backbone. The goal is quiet, repeatable compounding: small, steady buys into strong ETFs, once per week. We never average down, and we avoid dramatic allocation swings. Macro thinking (bull/sideways/bear) is already embedded in the Asset Allocator’s targets — S2 does not second-guess macro. Instead, S2 accepts the allocator’s destination and glides toward it calmly through time.


When risk rises or an instrument weakens later, we h
arvest small profits (only when green) and route proceeds to Defensive. Re-entry happens via the same weekly SIP method when health improves. This keeps emotions low and behavior consistent.

## **2) Where the Money Comes From — The Asset Allocator Link**
Each week, S2 receives a budget from the allocator. Conceptually, the allocator has already studied trend, volatility, and breadth and produced target weights for the whole portfolio. The difference between the current S2 weight and the allocator’s S2 target is the Gap\_to\_Target\_S2. To avoid shocks, we spread this gap across a fixed number of weeks so the journey is smooth.

Formula (₹):  Weekly\_S2\_Base\_Budget = Gap\_to\_Target\_S2(₹) ÷ Weeks\_to\_Glide

• Default Weeks\_to\_Glide = 52 (one year). You can tune this (e.g., 26 for faster, 78 for slower). A longer glide is gentler on the current holdings; a shorter glide adapts faster to new regimes.

• Final Monday budget (what we can spend) respects safety caps: Weekly\_S2\_Capacity = min( Weekly\_S2\_Base\_Budget, Weekly\_Transfer\_Cap\_% × Total\_Capital, S2\_Weekly\_Budget\_Cap\_% × Total\_Capital ).

• Optional Carry-Forward: If we don’t deploy the base budget because candidates fail health, we can carry it forward to an Accrued\_S2\_Carry bucket and deploy later within the same caps. This preserves the glide while honoring risk.
### **Example — Reading the Allocator & Setting the Weekly Budget**
Suppose S2 is at 28% and the allocator’s target is 34% → Gap\_to\_Target\_S2 = 6% of total capital. With Weeks\_to\_Glide = 52, the base budget equals ~0.115% of total capital per week. If the allocator’s Weekly\_Transfer\_Cap\_% is 5% and S2\_Weekly\_Budget\_Cap\_% is 1.25%, the min() is 0.115% — that becomes your Weekly\_S2\_Capacity before applying health and pacing rules.
## **3) ETF Lineup & Mix — How We Choose the Building Blocks**
S2 can host up to 10 ETFs: start with up to 8 core funds today (ETF\_01 … ETF\_08) and reserve 2 future slots (ETF\_09, ETF\_10). Assign each e`%% CBnabled %% ETF a target percentage of S2 so that enabled targets sum to 100%. You may keep it simple with equal weights, specify custom weights, or use a hybrid (equal within sub-buckets like Core Broad vs Satellite Factors).

Best practices when selecting ETFs:\
• Keep the core truly broad (e.g., large-cap or total-market). Avoid overstuffing factors.\
• Add satellites sparingly (mid/small/quality/low-vol/sector). Each must earn its slot.\
• Check tracking quality and liquidity (tight spreads, robust AUM).\
• Avoid overlapping exposures that secretly concentrate single sectors or mega-caps.

Risk caps (simple and effective):\
• Single-ETF Max: e.g., ≤ 35% of S2.\
• Tag/Sector Caps: e.g., Financials ≤ 25% of S2; PSU/Infra/Defensive ≤ 30%.\
• New ETF Ramp-In: temporarily cap a new ETF (e.g., ≤ 15% of S2 for 12 weeks) while it proves itself.
### **Example — A Clean 6-ETF Mix (sum to 100% of S2)**
Core Broad (70%): 40% Large-Cap Broad, 30% Total-Market Broad\
Satellites (30%): 10% Mid-Cap, 10% Quality, 10% Low-Volatility\
If you later add a small-cap factor (say 10%), you can reduce Core Broad to 60% and Satellites to 40% while keeping Single-ETF and Tag caps intact.
## **4) Health Checks — The Simple, No-Falling-Knife Test**
Because the allocator has handled macro, S2 only asks: “Is this ETF healthy enough to add this week?” We use a minimal set of weekly signals that play well together and are easy to audit.

Required signals (weekly):\
• TSI(25,13) > Signal, where Signal = EMA(7) of TSI — captures medium-term trend with smoothing.\
• RSI(14) > 50 — avoids buying weak momentum.\
• VWMA(20) slope ≥ 0 — ensures average price (weighted by volume) is not falling.\
• ATR% ≤ ATR\_Ceiling\_% — keeps adds to instruments with manageable volatility (default 2.0%; allow 2.5–3.0% per ETF override).

Why these work together:\
• TSI vs Signal is a robust trend confirmation with fewer whipsaws than price crosses alone.\
• RSI>50 nudges you to buy strength, not dips making lower-lows.\
	• VWMA slope checks that the market is accepting higher prices on real volume.\
• ATR% cap avoids deploying into chaotic tape.
### **Edge Cases — What If Only One Signal Fails?**
Keep the rules binary and simple (pass/fail). If an ETF fails any health test, skip it this week. This prevents second-guessing and protects the glide. If many ETFs fail in a difficult market, the carry-forward option preserves unused budget.
## **5) Pacing & Priority — Turning Budget into Orders**
Once Weekly\_S2\_Capacity is known and health is checked, deployment is straightforward. We favor the underweights, but we don’t force buys into weak ETFs.

Pacing logic:\
• UNDER & Health = 4 (very healthy) → buy a full slice.\
• UNDER & Health = 3 (healthy) → buy a half slice.\
• NEAR or OVER target → no buy.\
Tie-breakers (use one, keep it consistent): allocate first to lower ATR% (less noise) or to higher RSI (more momentum).

Compliance: Always respect Single-ETF Max and Tag/Sector Caps when allocating that week’s rupee budget. If compliance would be breached, scale down and re-distribute across other passing ETFs; if none qualify, do not spend.
## **6) Execution — How We Actually Place the Orders**
We submit Good-Till-Triggered (GTT) buy orders on Monday, using gentle pullbacks to avoid chasing. This keeps execution repeatable and removes emotion.

Default placement:\
• One GTT per ETF at ~0.5×ATR below Friday close. This usually gets filled within a normal weekly range if trend continues, and it protects us if price spikes at the open.

Optional two-step ladder (only if Health=4 and the ETF is materially UNDERweight):\
• Ladder 1: base level (~0.5×ATR below Friday close)\
• Ladder 2: Ladder 1 − 0.5×ATR\
Keep it to a maximum of two levels to avoid micromanagement; one action per ETF per week.

Hygiene:\
• GTTs expire by Friday close; anything not filled is reviewed next Monday.\
• Record each action (ETF, amount, price, reason). Logs make audits and tweaks far easier.
## **7) Defaults & Owner Knobs (Implemented by Designer)**
Budgeting:\
• Weeks\_to\_Glide: 52 (range 26–78)\
• Weekly\_Transfer\_Cap\_% (allocator): 5%\
• S2\_Weekly\_Budget\_Cap\_%: 1.0–1.5%\
• Carry\_Forward: ON/OFF

Lineup:\
• Up to 10 ETFs (8 active now + 2 future)\
• Single-ETF Max: ≤ 35% of S2 (example)\
• Tag/Sector Caps (examples): Financials ≤ 25%; PSU/Infra/Defensive ≤ 30%\
• Ramp-In for new ETFs: ≤ 15% of S2 for 12 weeks

Health:\
• TSI(25,13), Signal = EMA(7) of TSI\
• RSI(14) > 50; VWMA(20) slope ≥ 0\
• ATR\_Ceiling\_%: 2.0% default; 2.5–3.0% per-ETF override allowed
## **8) What Comes Next (Pointers to Parts 2 & 3)**
Part 2 covers profit-only harvesting: when (H1 stretch, H2 volatility spike, H3 health breakdown), how much (small trims with hard ceilings), and where the proceeds go (Defensive). Part 3 details the Monday Mix ritual, governance standards, logging, and a single summary table for the designer.

Bottom line: The allocator sets the destination and budget; S2 converts that into calm, weekly buys of healthy ETFs with a simple, auditable process.
