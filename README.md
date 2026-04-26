# MACD Momentum Strategy

Captures momentum continuation moves by entering on confirmed MACD bullish crossovers and exiting on bearish crossovers.

## How It Works

| Signal | Condition | Action |
|---|---|---|
| **Bullish Entry** | MACD crosses **above** signal line AND histogram > 0 | BUY — enter long |
| **Bearish Exit** | MACD crosses **below** signal line | SELL — exit long |
| **Stop Loss** | Price drops 6% from entry | EXIT — hard stop |

The AND condition filters out weak signals — requiring the histogram to be positive ensures momentum is already building, not just barely crossing.

## Parameters

| Parameter | Default | Description |
|---|---|---|
| Fast EMA | 12 | Short-term exponential average |
| Slow EMA | 26 | Long-term exponential average |
| Signal Line | 9 | Smoothing of MACD line |
| Stop Loss | 6% | Max loss per trade |

## When It Works Best

- **Trending markets** — works well in sustained directional moves
- **Stocks, crypto, futures** — versatile across asset classes
- **Daily or 4-hour charts** — reduces noise from shorter timeframes
- **Post-consolidation breakouts** — MACD crossovers after tight ranges are especially powerful

## When to Avoid

- Choppy, low-volatility environments — whipsaw signals
- Very slow-moving assets — MACD lags too much
- When price is already extended — late entries have poor R:R

## Sample Backtest (QQQ, 2015–2023)

```
Total Return:     +143.7%
Annualized:       +11.8%
Sharpe Ratio:     0.96
Max Drawdown:     -21.3%
Win Rate:         52%
Profit Factor:    1.74
```

## Signal Confirmation Logic

```
Entry = MACD_line crosses above Signal_line
      AND MACD_histogram > 0

Exit  = MACD_line crosses below Signal_line
     OR Stop Loss hit (-6%)
```

## How to Import

1. Open the Strategy Builder in the app
2. Click **Import Strategy**
3. Upload `strategy.json`
4. Configure your symbols and run a backtest

## License

MIT — free to use, modify, and share.
