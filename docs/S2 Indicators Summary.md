

---

## 📊 Core Indicators

| Indicator                                 | Purpose                                  | Parameters                                         | Signal Meaning                                                              |
| ----------------------------------------- | ---------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------- |
| **RSI (Relative Strength Index)**         | Momentum gauge                           | 14-period (weekly)                                 | RSI > 50 → bullish/healthy; RSI < 50 → weak/unhealthy                       |
| **TSI (True Strength Index)**             | Momentum confirmation, smoother than RSI | Typically (25, 13) with a 7-period EMA signal line | TSI > Signal → bullish; TSI < Signal → bearish                              |
| **VWMA (Volume Weighted Moving Average)** | Trend strength and slope check           | 20-period (weekly)                                 | Positive slope → healthy trend; negative slope → unhealthy                  |
| **ATR (Average True Range)**              | Volatility & risk sizing                 | 14-period (weekly)                                 | Used to compute ATR% = ATR / Close × 100 → must be below ceiling (e.g., 6%) |
| **ATR% (ATR as % of price)**              | Volatility filter                        | derived from ATR                                   | If above ceiling → ETF too volatile → excluded                              |
| **VWMA Slope**                            | Confirmation metric                      | derived from VWMA(20)                              | Positive slope means trend supportive                                       |

---

## ⚙️ Derived / Custom Metrics

| Metric                             | Source                              | Used For                                         |
| ---------------------------------- | ----------------------------------- | ------------------------------------------------ |
| **Health Check**                   | Combines RSI, TSI, VWMA slope, ATR% | ETF must pass all to be eligible                 |
| **Gap_to_Target_S2**               | Allocator data (Target% − Current%) | Drives buy sizing / rupee budget per ETF         |
| **ATR Ceiling%**                   | Config value                        | Maximum acceptable volatility for inclusion      |
| **VWMA Gradient / TSI Crossovers** | Derived triggers                    | Define buy/harvest points (H1/H2/H3 logic)       |
| **Weekly Drift Band**              | Config control                      | Prevents over-trading around small price changes |

---

## 🧠 Summary — in plain dev terms

The **indicator engine** in the pipeline computes four base things from weekly OHLCV:

- RSI(14)
    
- TSI(25,13) and its signal line (EMA(7))
    
- VWMA(20) and its slope
    
- ATR(14) → ATR%
    

Then **signal engine** just checks simple booleans:

```python
RSI > 50
TSI > Signal
VWMA_slope > 0
ATR_pct < ceiling
```

If all `True` → ETF is “healthy” and can be considered for buys this week.  
If any fail → ETF is skipped.

---

	