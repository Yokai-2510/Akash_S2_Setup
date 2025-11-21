Trading System — Categorized Indicator Library (Template-Aligned)

**Purpose:** Provide a comprehensive, categorized list of indicators to implement. Each entry follows the template: Why, Inputs, Params (variables to keep), Columns (outputs), Likely Strategies, Overlap & Notes. Use Overlap & Notes to prune duplicates when the stack becomes too heavy. Strategies named are indicative and may evolve.
# **Strategy Glossary (quick reference)**
• S1 — Cash Swing: Weekly/Daily pullbacks & trend-aligned breakouts with staged targets.

• S2 — Futures 4‑Lot (far‑month): Swing/position trades with ATR‑based stops and regime filters.

• ETF Pullback v5.0: BANKBEES/SILVERBEES, pullback entries via VWMA/RSI/ATR confluence.

• Defensive ETF v3.0: Bharat Bond + Gold/Silver sleeve; volatility/regime‑based dial‑up/down.

• WARR+ Alpha Momentum: Sector‑aware relative strength & 52‑week leadership ranking.
# **Trend & Moving Averages**
## **SMA / EMA (Fast, Slow, Anchor)**
**Why:** Backbone for trend direction, pullback magnets, and cross signals.

**Inputs:** Close.

**Params:** CFG\_DMA\_Fast, CFG\_DMA\_Slow, CFG\_EMA\_Fast, CFG\_EMA\_Anchor.

**Columns:** DMA\_Fast, DMA\_Slow, EMA\_Fast, EMA\_Anchor, Price>Anchor (bool), Cross\_Fast>Slow (bool).

**Likely Strategies:** S1, S2, ETF Pullback v5.0, Defensive ETF v3.0, WARR+.

**Overlap & Notes:** Overlap with VWMA as anchor; EMA slope often substitutes for trend state; MA Ribbon can be redundant.
## **EMA Slope (of Anchor)**
**Why:** Noise‑resistant trend state (Rising/Flat/Falling) used as a regime filter.

**Inputs:** EMA\_Anchor.

**Params:** CFG\_EMA\_SlopeDays.

**Columns:** EMA\_Slope, EMA\_Trend (Rising/Flat/Falling).

**Likely Strategies:** S1/S2 regime filter; ETF Pullback v5.0.

**Overlap & Notes:** Overlaps with Heikin Ashi trend state, Supertrend direction, and Ichimoku bias.
## **VWMA (Volume‑Weighted MA)**
**Why:** Trend anchor weighted by volume; excellent for ETF pullbacks.

**Inputs:** Close, Volume.

**Params:** CFG\_VWMA\_Len (e.g., 20/50).

**Columns:** VWMA, Price>VWMA (bool), VWMA\_Slope.

**Likely Strategies:** ETF Pullback v5.0, S1 trend alignment.

**Overlap & Notes:** Overlaps with EMA anchors; pick either EMA Anchor or VWMA Anchor to avoid duplication.
## **Heikin Ashi Trend State**
**Why:** Smoother candles to classify trend/pullback and reduce noise.

**Inputs:** Open, High, Low, Close.

**Params:** CFG\_HA\_Smooth (optional).

**Columns:** HA\_Open, HA\_Close, HA\_Trend (Up/Down), HA\_DoWick (bool).

**Likely Strategies:** S1 trend visual filter; S2 regime confidence.

**Overlap & Notes:** Can substitute for EMA slope in some screens; avoid using both as hard filters.
## **Ichimoku Cloud (optional)**
**Why:** All‑in‑one trend/momentum/levels framework (Tenkan/Kijun/Cloud/Chikou).

**Inputs:** High, Low, Close.

**Params:** CFG\_Ichi\_Tenkan, CFG\_Ichi\_Kijun, CFG\_Ichi\_Senkou.

**Columns:** Tenkan, Kijun, SpanA, SpanB, Chikou.

**Likely Strategies:** S1 swing trend; S2 trend following (optional).

**Overlap & Notes:** Covers multiple concepts (trend/levels/momentum); may overlap with MAs, Donchian, and support/resistance modules.
# **Momentum & Strength**
## **RSI (Wilder)**
**Why:** Mean‑reversion timing and momentum confirmation.

**Inputs:** Close.

**Params:** CFG\_RSI\_Len, CFG\_RSI\_Thresh.

**Columns:** RSI, RSI\_OK (≥ thresh), RSI\_State (OB/OS/Neutral).

**Likely Strategies:** S1 pullbacks, S2 timing, ETF Pullback v5.0.

**Overlap & Notes:** Functional overlap with Stoch, StochRSI, MFI; pick 1–2 to reduce noise.
## **Stochastic Oscillator**
**Why:** Overbought/oversold oscillator for timing within trends.

**Inputs:** High, Low, Close.

**Params:** CFG\_Stoch\_K, CFG\_Stoch\_D, CFG\_Stoch\_Smooth.

**Columns:** %K, %D, Stoch\_Cross (bool).

**Likely Strategies:** S1 timing; S2 fade control.

**Overlap & Notes:** Overlaps with RSI; if StochRSI used, consider dropping classic Stoch.
## **RSI Divergence (Regular & Hidden) — Equity**
Why: Spot momentum–price disagreement to time reversals or trend continuations on equities (ignore OI/options).

Inputs: Close (for Price), RSI (derived from Close).

Params (variables to keep): CFG\_RSI\_Len=14; CFG\_Div\_PivotL=2; CFG\_Div\_PivotR=2; CFG\_Div\_MinSepBars=3; CFG\_Div\_TolPct=0.5; CFG\_Div\_Lookback=100.

Columns (outputs): RSI; Price\_Pivot\_H; Price\_Pivot\_L; RSI\_Pivot\_H; RSI\_Pivot\_L; Div\_Reg\_Bull (bool); Div\_Reg\_Bear (bool); Div\_Hid\_Bull (bool); Div\_Hid\_Bear (bool); Div\_Score (0–100, optional); Div\_AgeBars (optional).

Likely Strategies (may evolve): S1 (Cash Swing) reversal timing; WARR+ continuation checks; ETF Pullback v5.0 fine-tune (equity ETFs).

Overlap & Notes: Redundant with MACD/StochRSI divergences—keep only one divergence module. Prefer signals with trend filter (e.g., EMA\_Anchor rising/falling) and RVOL>1 for confirmation.

**TSI (Trend Strength Index)**

**Why:** Double-smoothed momentum oscillator that measures both direction and persistence of trend strength; ideal for filtering noise on weekly timeframes.

**Inputs:** Close.

**Params:** CFG\_TSI\_Fast, CFG\_TSI\_Slow, CFG\_TSI\_Signal.

**Columns:** TSI\_Line, TSI\_Signal, TSI\_Hist, TSI\_Trend (Up/Down).

**Likely Strategies:** S1 long-term momentum filter; S2 trend confirmation; ETF Pullback v5.0 alpha enhancer; Defensive ETF v3.0 regime validation.

**Overlap & Notes:** Complements RSI, TRIX, and MACD; use when smoother, trend-persistent confirmation is preferred. Avoid redundancy if TRIX or PPO already used.
## **Stochastic RSI**
**Why:** Sensitivity‑boosted RSI for early turns.

**Inputs:** RSI (derived).

**Params:** CFG\_StochRSI\_Len.

**Columns:** StochRSI, StochRSI\_Signal.

**Likely Strategies:** S1 pullback timing; S2 micro‑timing.

**Overlap & Notes:** High overlap with RSI and Stoch; keep only if you value higher sensitivity.
## **Rate of Change (ROC)**
**Why:** Momentum strength across horizons for ranking.

**Inputs:** Close.

**Params:** CFG\_ROC\_Fast, CFG\_ROC\_Slow.

**Columns:** ROC\_Fast\_%, ROC\_Slow\_%.

**Likely Strategies:** WARR+ ranking, S1/S2 momentum confirm.

**Overlap & Notes:** Overlaps with PPO, TRIX for momentum slope; choose 1–2 families.
## **MACD**
**Why:** Blend of trend and momentum using EMAs; cross/zero‑line logic.

**Inputs:** Close.

**Params:** CFG\_MACD\_Fast, CFG\_MACD\_Slow, CFG\_MACD\_Signal.

**Columns:** MACD\_Line, MACD\_Signal, MACD\_Hist, MACD\_Cross (bool).

**Likely Strategies:** Defensive ETF v3.0 regime, S1 confirmation.

**Overlap & Notes:** Overlap with PPO (scale‑invariant MACD); prefer PPO for cross‑asset comparability.
## **PPO (Percentage Price Oscillator)**
**Why:** MACD in percentage terms; better for comparing instruments.

**Inputs:** Close.

**Params:** CFG\_PPO\_Fast, CFG\_PPO\_Slow, CFG\_PPO\_Signal.

**Columns:** PPO\_Line, PPO\_Signal, PPO\_Hist.

**Likely Strategies:** WARR+ ranking, Defensive ETF v3.0 regime.

**Overlap & Notes:** Overlap with MACD; pick one to avoid redundancy.
## **TRIX**
**Why:** Triple‑smoothed momentum to reduce noise (weekly friendly).

**Inputs:** Close.

**Params:** CFG\_TRIX\_Len, CFG\_TRIX\_Signal.

**Columns:** TRIX, TRIX\_Signal, TRIX\_Hist.

**Likely Strategies:** S1 weekly momentum filter; Defensive ETF v3.0.

**Overlap & Notes:** Overlaps with MACD/PPO; keep if you want extra smoothing.
## **ADX / DMI**
**Why:** Trend strength and directional bias (+DI/‑DI).

**Inputs:** High, Low, Close.

**Params:** CFG\_ADX\_Period.

**Columns:** ADX, +DI, -DI, ADX\_Trend (Strong/Weak).

**Likely Strategies:** S1 continuation, S2 filter, WARR+ ranking.

**Overlap & Notes:** Complements momentum oscillators; limited overlap.
## **Williams %R**
**Why:** Fast OB/OS similar to Stochastic.

**Inputs:** High, Low, Close.

**Params:** CFG\_WPR\_Len.

**Columns:** WPR, WPR\_State.

**Likely Strategies:** S1 timing; ETF pullback add‑on.

**Overlap & Notes:** High overlap with Stoch; keep only one.
## **CCI**
**Why:** Deviation from mean; useful for range breaks.

**Inputs:** Typical Price.

**Params:** CFG\_CCI\_Len.

**Columns:** CCI, CCI\_State (OB/OS).

**Likely Strategies:** S1 breakouts; S2 confirm.

**Overlap & Notes:** Overlaps with RSI/Stoch in purpose, but different math—optional.
## **RVI (Relative Vigor Index)**
**Why:** Conviction comparing close vs open relative to range.

**Inputs:** Open, High, Low, Close.

**Params:** CFG\_RVI\_Len.

**Columns:** RVI, RVI\_Signal.

**Likely Strategies:** S1 continuation confirmation.

**Overlap & Notes:** Niche; drop if stack is heavy.
# **Volatility & Bands**
## **ATR (Wilder) — Core Risk Metric**
**Why:** Volatility unit for position sizing, pullback depth and stop ladders.

**Inputs:** High, Low, Close.

**Params:** CFG\_ATR\_Len.

**Columns:** ATR\_N, ATR\_% (ATR/Close\*100).

**Likely Strategies:** Core risk engine for S1 & S2; ETF Pullback v5.0.

**Overlap & Notes:** Foundational (keep).
## **ATR Trailing Stop (Chandelier variant)**
**Why:** Dynamic stop anchored to extremes with ATR multiple.

**Inputs:** High, Low, Close, ATR.

**Params:** CFG\_ATR\_StopMult, CFG\_ATR\_LkbHiLo.

**Columns:** ATR\_Stop\_Long, ATR\_Stop\_Short, Stop\_Flip (bool).

**Likely Strategies:** S1/S2 trailing; ETF protection.

**Overlap & Notes:** Overlaps with Supertrend/PSAR; pick one trailing family.
## **Bollinger Bands**
**Why:** Mean‑reversion envelope & squeeze detection.

**Inputs:** Close.

**Params:** CFG\_BB\_Period, CFG\_BB\_Std.

**Columns:** BB\_Mid, BB\_Upper, BB\_Lower, %B, BandWidth.

**Likely Strategies:** S1 pullbacks/squeezes; ETF Pullback v5.0.

**Overlap & Notes:** Overlaps with Keltner; both needed only for squeeze logic.
## **Keltner Channels**
**Why:** ATR‑based envelopes for trend pullbacks; complements BB.

**Inputs:** EMA + ATR.

**Params:** CFG\_KC\_Period, CFG\_KC\_ATRmult.

**Columns:** KC\_Mid, KC\_Upper, KC\_Lower.

**Likely Strategies:** S1 pullbacks; Squeeze detector (BB inside KC).

**Overlap & Notes:** Mostly used alongside BB for squeeze; drop if not using squeeze logic.
## **Donchian Channels**
**Why:** Breakout & trailing logic (Turtle‑style).

**Inputs:** High, Low.

**Params:** CFG\_Donch\_Period.

**Columns:** Donch\_Hi, Donch\_Lo, Donch\_Width.

**Likely Strategies:** S1 breakouts; WARR+ momentum; S2 continuation.

**Overlap & Notes:** Overlaps with Fractals/Structure for HH/HL/LH/LL.
## **Squeeze (BB inside KC)**
**Why:** Low‑volatility compression likely to expand.

**Inputs:** BB & KC outputs.

**Params:** CFG\_Sqz\_MinDays.

**Columns:** Sqz\_On (bool), Sqz\_Fire (bool).

**Likely Strategies:** S1 squeeze breakouts; S2 ignition.

**Overlap & Notes:** Depends on both BB and KC; remove if not using squeeze setups.
# **Volume & Flow**
## **On‑Balance Volume (OBV) & Slope**
**Why:** Volume confirmation of trend and breakouts.

**Inputs:** Close, Volume.

**Params:** CFG\_OBV\_SlopeDays.

**Columns:** OBV, OBV\_Slope, OBV\_Trend.

**Likely Strategies:** S1 confirm, ETF flows, S2 momentum.

**Overlap & Notes:** Overlaps with A/D and CMF; pick 1–2.
## **Money Flow Index (MFI)**
**Why:** Volume‑weighted RSI to gauge pressure.

**Inputs:** High, Low, Close, Volume.

**Params:** CFG\_MFI\_Len.

**Columns:** MFI, MFI\_State.

**Likely Strategies:** ETF Pullback v5.0; Defensive ETF v3.0.

**Overlap & Notes:** Overlap with RSI + Volume; choose either MFI or CMF.
## **Chaikin Money Flow (CMF)**
**Why:** Flow pressure combining price location and volume.

**Inputs:** High, Low, Close, Volume.

**Params:** CFG\_CMF\_Len.

**Columns:** CMF, CMF\_Trend.

**Likely Strategies:** ETF flows, S1 confirmation.

**Overlap & Notes:** Overlaps with MFI/A/D; pick one.
## **Accumulation/Distribution (Chaikin A/D)**
**Why:** Cumulative flow proxy (accumulation vs distribution).

**Inputs:** High, Low, Close, Volume.

**Params:** CFG\_AD\_Smooth (optional).

**Columns:** AD\_Line, AD\_Slope.

**Likely Strategies:** S1, Defensive ETF v3.0 flow bias.

**Overlap & Notes:** Overlaps with OBV/CMF; choose 1–2 max.
## **Relative Volume (RVOL) & Volume Spike**
**Why:** Detect unusual participation and event‑driven spikes.

**Inputs:** Volume.

**Params:** CFG\_RVOL\_Lkb, CFG\_VolSpike\_Lkb, CFG\_VolSpike\_Z.

**Columns:** RVOL, RVOL\_Z, VolSpike (bool), Vol\_Zscore.

**Likely Strategies:** S1 breakouts, S2 ignition, ETF events.

**Overlap & Notes:** Distinct utility; generally keep.
# **Liquidity & Tradeability**
## **Spread Proxy & ADV**
**Why:** Filter illiquid instruments and wide spreads.

**Inputs:** High, Low, Close, Volume, Value.

**Params:** CFG\_Spread\_Lkb, CFG\_ADV\_Lkb, CFG\_ADV\_TopN.

**Columns:** SpreadProxy, ADV\_Lkb\_Vol, ADV\_Lkb\_Value, Rank\_ADV\_Value, InTopN (bool).

**Likely Strategies:** ETF systems, S2 instrument selection.

**Overlap & Notes:** Unique; keep for execution quality.
# **Market Structure & Price Action**
## **Swing High/Low (Fractals) & Structure**
**Why:** Identify HH/HL/LH/LL and structure breaks (BOS/CHOCH).

**Inputs:** High, Low.

**Params:** CFG\_Fractal\_L, CFG\_Fractal\_R.

**Columns:** Swing\_Hi, Swing\_Lo, BOS (bool), CHOCH (bool).

**Likely Strategies:** S1 structure entries/exits; S2 trend confirms.

**Overlap & Notes:** Overlaps with Donchian for breakouts.
## **Supertrend (ATR‑based regime/stop)**
**Why:** Simple trailing stop and regime tag.

**Inputs:** High, Low, Close.

**Params:** CFG\_ST\_Period, CFG\_ST\_Mult.

**Columns:** ST\_Value, ST\_Dir (UP/DOWN).

**Likely Strategies:** S1 & S2 trailing; ETF confirmation.

**Overlap & Notes:** Overlaps with ATR trailing and PSAR; pick one family.
## **Parabolic SAR (PSAR)**
**Why:** Adaptive trailing stop for trending moves.

**Inputs:** High, Low, Close.

**Params:** CFG\_PSAR\_AF, CFG\_PSAR\_AFmax.

**Columns:** PSAR, PSAR\_Flip (bool).

**Likely Strategies:** S1/S2 trailing alternative.

**Overlap & Notes:** Overlap with Supertrend/ATR trailing.
## **Pivot Points (Std/Fibonacci)**
**Why:** Widely watched levels for reactions and targets.

**Inputs:** Prior High, Low, Close.

**Params:** CFG\_Pivot\_Mode, CFG\_Pivot\_Frame.

**Columns:** PP, S1/S2/S3, R1/R2/R3.

**Likely Strategies:** S2 swing levels; S1 target confluence.

**Overlap & Notes:** Overlaps with Fib/AVWAP/VP as levels; pick few.
## **Gap Detector (Up/Down)**
**Why:** Capture NSE gap dynamics to adjust entries/risk.

**Inputs:** Open, Prior Close.

**Params:** CFG\_Gap\_MinPct.

**Columns:** Gap\_Up(bool), Gap\_Down(bool), Gap\_% .

**Likely Strategies:** S1/S2 gap rules; ETF dip filters.

**Overlap & Notes:** Unique; keep if gaps affect entries.
# **Relative Performance & Ranking**
## **Relative Strength vs Benchmark**
**Why:** Out/under‑performance vs NIFTY or category benchmark.

**Inputs:** Asset Close + Benchmark Close.

**Params:** CFG\_RS\_Benchmark, CFG\_RS\_Lkb.

**Columns:** RS\_Ratio, RS\_Momentum, RS\_Rank.

**Likely Strategies:** WARR+ ranking; S1 rotation; Defensive ETF tilt.

**Overlap & Notes:** May overlap with ROC‑based ranks; pick core metric.
## **52‑Week High/Low & Percentile**
**Why:** Long‑term strength filter and anchors for profit bands.

**Inputs:** High, Low, Close.

**Params:** CFG\_YearCandles (e.g., 252).

**Columns:** Hi\_52W, Lo\_52W, Pct\_to\_Hi, Pct\_from\_Lo, Close\_52W\_Pctl.

**Likely Strategies:** WARR+ momentum, S1 continuation, ETF profit bands.

**Overlap & Notes:** Works with RS; little direct overlap.
# **Levels & Anchors (Price & Volume)**
## **Anchored VWAP (AVWAP)**
**Why:** Event‑anchored fair‑value (52W high/low, regime start, earnings).

**Inputs:** Typical Price, Volume, Anchor Date.

**Params:** CFG\_AVWAP\_Anchor, CFG\_AVWAP\_Reset.

**Columns:** AVWAP, Price‑to‑AVWAP %, AVWAP\_Slope.

**Likely Strategies:** S1/S2 pullback & reclaim logic; ETF anchors.

**Overlap & Notes:** Overlaps with Volume Profile for support/resistance—use AVWAP when anchors are known.
## **Volume Profile (Fixed Range / Session)**
**Why:** Volume‑at‑price distribution: POC/HVNs/LVNs & value area.

**Inputs:** Price‑level volume (intraday best).

**Params:** CFG\_VP\_AnchorDate, CFG\_VP\_Bins, CFG\_VP\_Lkb, CFG\_VP\_Mode.

**Columns:** VP\_POC, VP\_HVNs, VP\_LVNs, VP\_ValueArea bounds.

**Likely Strategies:** S2 and S1 confluence zones; ETF anchors if available.

**Overlap & Notes:** Overlaps with AVWAP; pick based on data availability and timeframe.
## **Fibonacci Retracement Zones**
**Why:** Common pullback/extension zones for confluence and targets.

**Inputs:** Swing points (hi/lo).

**Params:** CFG\_Fib\_Use (0.236/0.382/0.5/0.618/0.786), CFG\_Fib\_Ext (1.272/1.618).

**Columns:** Fib\_Levels, Fib\_Touch(bool).

**Likely Strategies:** S1 target/pullback confluence; S2 scaling.

**Overlap & Notes:** Overlaps with Pivots/AVWAP/VP as level sets; keep few.
## **Round Number Proximity**
**Why:** Psychological levels (₹50/₹100/₹500 steps) for reactions.

**Inputs:** Close.

**Params:** CFG\_Round\_Step (₹).

**Columns:** Round\_Level, Dist\_to\_Round\_% .

**Likely Strategies:** S1 fine‑tuning; S2 exits.

**Overlap & Notes:** Lightweight; keep optional.
# **Regime & Risk**
## **Volatility Regime (Index‑linked)**
**Why:** Market risk state via India VIX or realized vol proxy.

**Inputs:** VIX series or ATR% / HV%.

**Params:** CFG\_VIX\_Thresh\_Hi, CFG\_VIX\_Thresh\_Lo (or HV% thresholds).

**Columns:** Regime (Calm/Normal/High), RiskBudget (Low/Med/High).

**Likely Strategies:** Defensive ETF v3.0, S2 sizing.

**Overlap & Notes:** Optional if VIX not integrated.
## **ATR‑Based Position Size**
**Why:** Contracts/shares sized so risk per trade is controlled.

**Inputs:** ATR\_N, Entry, Stop, Risk per trade.

**Params:** CFG\_Risk\_PerTrade\_%Eq, CFG\_MinLot, CFG\_RoundLot.

**Columns:** Pos\_Size, Risk\_Rs, Risk\_%Eq.

**Likely Strategies:** Core for S1 & S2; ETF allocations (tactical).

**Overlap & Notes:** Uses ATR; not redundant.
# **Patterns Library — Candlesticks (Boolean flags)**
## **Candlestick Core Suite**
**Why:** Discrete reversal/continuation cues; use with trend/volume confirmation.

**Inputs:** Open, High, Low, Close (+ Volume optional).

**Params:** CFG\_Pattern\_Lkb, CFG\_BodyPctMin, CFG\_ShadowRatioMin, CFG\_EngulfPct, CFG\_GapConfirm.

**Columns:** Engulfing\_Bull/Bear, Harami\_Bull/Bear, PiercingLine, DarkCloudCover, MorningStar, EveningStar, Hammer, InvertedHammer, HangingMan, ShootingStar, Doji, DragonflyDoji, GravestoneDoji, Marubozu\_Bull/Bear, SpinningTop, Tweezer\_Top/Bottom, InsideBar, OutsideBar, BeltHold\_Bull/Bear, ThreeWhiteSoldiers, ThreeBlackCrows, PinBar\_Bull/Bear.

**Likely Strategies:** S1 reversal timing; S2 entry micro‑timing; ETF Pullback v5.0 fine‑tune.

**Overlap & Notes:** High overlap inside the suite; enable only 5–8 patterns you actually use.
# **Patterns Library — Chart Patterns (Price structure + Volume confirmation)**
## **Cup and Handle**
**Why:** Bullish base with U‑shaped cup and shallow handle; breakout above handle high.

**Inputs:** Close, High, Low, Volume.

**Params:** CFG\_Cup\_MinLen, CFG\_Cup\_DepthMax%, CFG\_Handle\_DepthMax%, CFG\_BreakoutBuffer%.

**Columns:** Pat\_CupHandle(bool), Cup\_Depth%, Handle\_Depth%, Breakout\_Lvl, Vol\_Confirm(bool).

**Likely Strategies:** S1 breakouts; WARR+ continuation.

**Overlap & Notes:** Overlaps with Rounding Bottom + Flag; keep one if redundancy arises.
## **Inverted Cup and Handle**
**Why:** Bearish counterpart for shorts or exit warnings.

**Inputs:** Close, High, Low, Volume.

**Params:** CFG\_iCup\_MinLen, CFG\_iCup\_DepthMax%, CFG\_Handle\_DepthMax%.

**Columns:** Pat\_iCupHandle(bool), iCup\_Depth%, Handle\_Depth%, Breakdown\_Lvl.

**Likely Strategies:** S2 short/hedge timing; S1 exit signals.

**Overlap & Notes:** Overlap with H&S; choose one bearish pattern family.
## **Head and Shoulders**
**Why:** Classic topping/bottoming structure with neckline break.

**Inputs:** Close, High, Low, Volume.

**Params:** CFG\_HS\_SymmetryTol, CFG\_NecklineSlopeTol, CFG\_MinShoulderSep.

**Columns:** Pat\_HS(bool), Neckline\_Lvl, Target\_Range, Vol\_Distribution\_Score.

**Likely Strategies:** S1 exits/shorts; S2 reversals.

**Overlap & Notes:** Overlaps with Double/Triple Top; keep 1–2 tops family.
## **Double Top / Double Bottom**
**Why:** Two failed attempts at breaking prior extreme; neckline/baseline break.

**Inputs:** Close, High, Low, Volume.

**Params:** CFG\_DT\_MinSepBars, CFG\_DT\_PriceTol%.

**Columns:** Pat\_DoubleTop(bool)/DoubleBottom(bool), Neckline\_Lvl, Target\_Range.

**Likely Strategies:** S1 exits/entries; S2 reversals.

**Overlap & Notes:** Overlaps with H&S/Triple Top/Bottom; pick essentials.
## **Triple Top / Triple Bottom**
**Why:** Three failed attempts; stronger pattern variant.

**Inputs:** Close, High, Low, Volume.

**Params:** CFG\_TT\_MinSepBars, CFG\_TT\_PriceTol%.

**Columns:** Pat\_TripleTop(bool)/TripleBottom(bool), Neckline\_Lvl.

**Likely Strategies:** S2 reversals; S1 exits.

**Overlap & Notes:** Overlaps with Double Top/Bottom; keep if needed.
## **Ascending / Descending / Symmetrical Triangle**
**Why:** Consolidation with contracting range; breakout often trend‑aligned.

**Inputs:** High, Low, Close, Volume.

**Params:** CFG\_Tri\_MinTouches, CFG\_Tri\_SlopeTol, CFG\_Tri\_MaxLen.

**Columns:** Pat\_Triangle(type), Breakout\_Lvl, Vol\_Squeeze\_Score.

**Likely Strategies:** S1 continuation; S2 breakout entries.

**Overlap & Notes:** Overlaps with Wedges; pick either Triangles or Wedges.
## **Flags & Pennants**
**Why:** Sharp pole move followed by small channel/triangle; continuation.

**Inputs:** Close, Volume.

**Params:** CFG\_Flag\_MaxDepth%, CFG\_Flag\_MaxLen, CFG\_Pole\_MinMove%.

**Columns:** Pat\_Flag/Pennant(bool), Pole\_%Move, Breakout\_Lvl, Vol\_Confirm(bool).

**Likely Strategies:** S1 continuation; S2 momentum ignition.

**Overlap & Notes:** Overlaps with High‑Tight Flag (HTF); keep HTF only if you target explosive moves.
## **High‑Tight Flag (HTF)**
**Why:** Explosive variant: ~100% pole in <8 weeks then tight flag.

**Inputs:** Close, Volume.

**Params:** CFG\_HTF\_PoleMin%, CFG\_HTF\_MaxWeeks, CFG\_HTF\_FlagDepth%.

**Columns:** Pat\_HTF(bool), Pole\_%Move, Breakout\_Lvl.

**Likely Strategies:** WARR+ high momentum; S1 continuation.

**Overlap & Notes:** Subset of Flags; keep only one of Flag/HTF if simplifying.
## **Wedges (Rising/Falling)**
**Why:** Contracting structure with converging trendlines; break favors trend direction.

**Inputs:** High, Low, Close.

**Params:** CFG\_Wedge\_MinTouches, CFG\_Wedge\_SlopeTol, CFG\_Wedge\_MaxLen.

**Columns:** Pat\_Wedge(type), Break\_Level, Slope\_Metrics.

**Likely Strategies:** S1 reversals/continuations; S2 entries.

**Overlap & Notes:** Overlaps with Triangles; choose one family.
## **Rectangles (Ranges)**
**Why:** Horizontal consolidations; breakout in either direction.

**Inputs:** High, Low, Close, Volume.

**Params:** CFG\_Rect\_MinTouches, CFG\_Rect\_MaxLen.

**Columns:** Pat\_Rectangle(bool), Range\_Hi, Range\_Lo, Breakout\_Lvl.

**Likely Strategies:** S1 continuation; S2 range breakouts.

**Overlap & Notes:** Overlaps with Donchian/Fractals for ranges.
## **Rounding Bottom / Saucer**
**Why:** Gradual curvature base; long consolidations with accumulation.

**Inputs:** Close, Volume.

**Params:** CFG\_Round\_MinLen, CFG\_Round\_DepthMax%.

**Columns:** Pat\_RoundingBottom(bool), Base\_Depth%, Breakout\_Lvl.

**Likely Strategies:** S1 base breakouts; ETF longer bases.

**Overlap & Notes:** Overlaps with Cup (no handle) and Cup & Handle.
## **Broadening Formations (Megaphone)**
**Why:** Expanding highs/lows; volatile and tricky; avoid or size down.

**Inputs:** High, Low, Close.

**Params:** CFG\_Broad\_MinTouches, CFG\_Broad\_SlopeTol.

**Columns:** Pat\_Broadening(bool), Upper\_Line, Lower\_Line.

**Likely Strategies:** Risk management awareness; not a primary entry signal.

**Overlap & Notes:** Distinct; keep optional.
## **Diamond Top/Bottom**
**Why:** Rare reversal pattern with broadening then narrowing ranges.

**Inputs:** High, Low, Close.

**Params:** CFG\_Diamond\_MinLen, CFG\_Diamond\_SymmetryTol.

**Columns:** Pat\_Diamond(bool), Break\_Level.

**Likely Strategies:** S2 reversals; S1 exits.

**Overlap & Notes:** Optional due to rarity.
# **Helpers — Gap & Squeeze (Already referenced)**
## **Gap Handling Rules**
**Why:** Rule set to modify entries/exits when gaps occur (slippage control).

**Inputs:** Gap flags, ATR, pre‑gap trend state.

**Params:** CFG\_Gap\_MinPct, CFG\_Gap\_SlipAdj, CFG\_Gap\_EntryDelayBars.

**Columns:** Gap\_Adjusted\_Entry, Gap\_SlipAdj\_Rs.

**Likely Strategies:** S1/S2 execution hygiene.

**Overlap & Notes:** Works with Gap Detector; unique role.
## **Squeeze Strength Score**
**Why:** Composite of BandWidth, KC distance, RVOL contraction.

**Inputs:** BB, KC, Volume.

**Params:** CFG\_Sqz\_Weights (BW/KC/RVOL).

**Columns:** Sqz\_Strength (0–100).

**Likely Strategies:** S1 breakout quality; S2 ignition.

**Overlap & Notes:** Derived metric; optional.

**Implementation Notes:** Params are named as CFG\_\* for seamless mapping to your Google Sheets config. Use Overlap & Notes to prune (e.g., pick PPO or MACD; RSI or StochRSI; BB or KC unless using squeeze). Pattern detection can start as boolean flags and later gain quality scores.


# <a name="_heading=h.hvn23vjzgwdm"></a>**Derivatives & Open Interest (OI) — Optional Module**
## <a name="_heading=h.2pqjxbg4r3x3"></a>**Open Interest (OI) — Level & Change**
**Why:** Core derivative participation metric. Rising OI with trend implies positioning; falling OI suggests de‑risking.

**Inputs:** OI series per instrument/expiry.

**Params:** CFG\_OI\_Smooth (days), CFG\_OI\_ChangeLkb (e.g., 1/5/10).

**Columns:** OI, OI\_Δ1, OI\_Δ5, OI\_Δ10, OI\_%Δ, OI\_Slope.

**Likely Strategies:** S2 futures entries/exits; S1 context; ETF (rare).

**Overlap & Notes:** Distinct; foundation for all OI logic.
## <a name="_heading=h.qav9fq77ku5g"></a>**Price–OI Quadrant (LSBU/SC/LU/SB)**
**Why:** Classify sessions into Long Build‑Up (↑Price, ↑OI), Short Covering (↑Price, ↓OI), Long Unwinding (↓Price, ↓OI), Short Build‑Up (↓Price, ↑OI).

**Inputs:** Close, OI.

**Params:** CFG\_LSBU\_Thresh\_% (price), CFG\_OI\_Thresh\_% (change).

**Columns:** Quadrant (LB/SC/LU/SB), Quad\_Score (‑2..+2).

**Likely Strategies:** S2 timing & filter; S1 context.

**Overlap & Notes:** Overlaps with volume‑price analysis; complementary.
## <a name="_heading=h.x0h0lbjexyj2"></a>**Futures Basis & Cost of Carry (CoC)**
**Why:** Premium/discount vs spot and carry; helps detect funding pressure and sentiment.

**Inputs:** Spot Close, Futures Close, Days\_to\_Expiry, Risk‑free rate (optional).

**Params:** CFG\_CoC\_Mode (simple/annualized), CFG\_Rf\_% (optional).

**Columns:** Basis = Fut‑Spot, Basis\_%=Basis/Spot, CoC\_% annualized.

**Likely Strategies:** S2 regime/timing; Defensive ETF hedging awareness.

**Overlap & Notes:** Basis overlaps with AVWAP/levels only as context—keep.
## <a name="_heading=h.zhzyytud9czd"></a>**Rollover Metrics (Near→Next/Far)**
**Why:** Measures how much OI is carried forward; detects conviction and positioning into new series.

**Inputs:** OI by expiry (near/next/far).

**Params:** CFG\_Roll\_Window (d), CFG\_Roll\_Min%

**Columns:** Rollover\_% (Near→Next), Rollover\_Score.

**Likely Strategies:** S2 series transition management.

**Overlap & Notes:** Data‑dependent; keep if expiry‑cycle logic is used.
## <a name="_heading=h.b3f1h2jr19ov"></a>**Participant Positioning (FII/DII/Prop/Client) — Optional**
**Why:** Top‑down lens on who is building positions (if data feed available).

**Inputs:** Participant OI/Volume long/short by futures/options.

**Params:** CFG\_Part\_Use (bool), CFG\_Part\_Smooth (d).

**Columns:** FII\_Net\_Long%, DII\_Net\_Long%, Prop/Client metrics.

**Likely Strategies:** S2 macro‑filter; Defensive ETF risk tone.

**Overlap & Notes:** External dependency (NSE participant files); optional.
## <a name="_heading=h.4wc98ercuekd"></a>**Put/Call Ratio (PCR) — OI & Volume**
**Why:** Crowding/contrarian context for indices and liquid stocks.

**Inputs:** Options OI & Volume by puts and calls (aggregate).

**Params:** CFG\_PCR\_Mode (OI/Vol), CFG\_PCR\_Smooth (d).

**Columns:** PCR\_OI, PCR\_Vol, PCR\_Zscore.

**Likely Strategies:** S2 index futures timing; Defensive ETF hedging tone.

**Overlap & Notes:** Noisy at extremes; pair with IV Rank.
## <a name="_heading=h.t50siwloyfo9"></a>**Implied Volatility (IV), IV Rank & IV Percentile**
**Why:** Volatility regime for options; informs risk sizing and timing of breakouts.

**Inputs:** Option chain or ATM IV time series.

**Params:** CFG\_IV\_Smooth, CFG\_IVRank\_Lkb (252).

**Columns:** IV\_ATM, IV\_Rank (0‑100), IV\_Percentile (0‑100), IV\_Δ.

**Likely Strategies:** S2 timing; Defensive ETF risk stance.

**Overlap & Notes:** Distinct from ATR (realized vol); keep both.
## <a name="_heading=h.3zbwyxsno73"></a>**Skew & Term Structure**
**Why:** Risk pricing across strikes/maturities; detects stress or complacency.

**Inputs:** IV by strike (OTM put/call) and across expiries.

**Params:** CFG\_Skew\_StrikeOffset, CFG\_Term\_Buckets.

**Columns:** Skew (Put‑Call IV), Term\_Slope (near→far).

**Likely Strategies:** S2 risk filter; hedge timing.

**Overlap & Notes:** Advanced/optional; data availability needed.
## <a name="_heading=h.xe9ye7m0f5ji"></a>**Max Pain & OI by Strike (Heatmap)**
**Why:** Pinning and congestion zones; potential magnet into expiry.

**Inputs:** Options OI by strike for current expiry.

**Params:** CFG\_MP\_Expiry, CFG\_OIHeat\_Bins.

**Columns:** MaxPain\_Strike, OI\_Heatmap (table ref).

**Likely Strategies:** S2 expiry‑week adjustments; not a primary signal.

**Overlap & Notes:** Heuristic; use cautiously and with price action.
## <a name="_heading=h.3d3n6y30ggrh"></a>**Gamma Exposure (GEX) & Key Levels — Advanced**
**Why:** Dealer gamma regime (positive/negative) can influence intraday trendiness.

**Inputs:** Option greeks by strike (requires model/data feed).

**Params:** CFG\_GEX\_Method, CFG\_GEX\_Smooth.

**Columns:** Net\_GEX, Flip\_Levels, GEX\_Sig.

**Likely Strategies:** S2 intraday bias (advanced).

**Overlap & Notes:** Data/model heavy; optional module.
## <a name="_heading=h.11bqdyqt0jkc"></a>**Options Volume Spike Detector**
**Why:** Detects unusual options activity that can precede moves.

**Inputs:** Options volume by strike/expiry.

**Params:** CFG\_OptVol\_Lkb, CFG\_OptVol\_Z.

**Columns:** OptVol\_Zscore, UnusualActivity (bool).

**Likely Strategies:** S2 momentum ignition; event watch.

**Overlap & Notes:** Pairs with RVOL in cash market.

