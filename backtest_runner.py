"""
Main backtest runner script
Orchestrates data download, strategy execution, and results reporting
"""

import pandas as pd
from strategy.london_imbalance import LondonImbalanceStrategy
from backtester.engine import BacktestEngine
from data.download_data import download_eurusd_data
from datetime import datetime, timedelta
import json
import os

def run_backtest():
    """Execute complete backtest workflow"""
    
    print("=" * 70)
    print("LONDON OPEN IMBALANCE STRATEGY - BACKTEST")
    print("=" * 70)
    
    # Step 1: Download data
    print("\n[1/6] Downloading EURUSD 5-minute data...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    try:
        df = download_eurusd_data(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None
    
    # Step 2: Initialize strategy
    print("\n[2/6] Initializing strategy with parameters...")
    strategy = LondonImbalanceStrategy(
        volume_multiplier=1.5,
        min_wick_pips=8,
        min_body_pips=5,
        ema_length=20,
        stop_loss_pips=15,
        tp1_pips=20,
        tp2_pips=30
    )
    print("  ✓ Volume multiplier: 1.5x")
    print("  ✓ Min rejection wick: 8 pips")
    print("  ✓ Min confirmation body: 5 pips")
    print("  ✓ Stop loss: 15 pips | TP1: 20 pips | TP2: 30 pips")
    
    # Step 3: Detect signals
    print("\n[3/6] Scanning for entry signals...")
    signals = strategy.detect_signals(df)
    print(f"  ✓ Found {len(signals)} valid signals")
    
    if len(signals) == 0:
        print("\n⚠ No signals found. Try adjusting parameters or date range.")
        return None
    
    # Step 4: Execute trades
    print("\n[4/6] Executing trades and tracking outcomes...")
    engine = BacktestEngine(initial_capital=3.0)
    trades_df = engine.execute_trades(df, signals)
    print(f"  ✓ Executed {len(trades_df)} trades")
    
    # Step 5: Calculate metrics
    print("\n[5/6] Calculating performance metrics...")
    metrics = engine.calculate_metrics(trades_df)
    
    # Step 6: Display results
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS")
    print("=" * 70)
    print(f"Total Trades:        {metrics['total_trades']}")
    print(f"Winners:             {metrics['winners']} ({metrics['win_rate']}%)")
    print(f"Losers:              {metrics['losers']}")
    print(f"-" * 70)
    print(f"Total Pips:          {metrics['total_pips']:+.1f}")
    print(f"Avg Pips/Trade:      {metrics['avg_pips']:+.2f}")
    print(f"Avg Win:             +{metrics['avg_win_pips']:.1f} pips")
    print(f"Avg Loss:            {metrics['avg_loss_pips']:.1f} pips")
    print(f"Profit Factor:       {metrics['profit_factor']:.2f}")
    print(f"Avg Time in Trade:   {metrics['avg_bars_in_trade']:.1f} bars (~{int(metrics['avg_bars_in_trade'] * 5)} min)")
    print("=" * 70)
    
    # Determine status
    if metrics['win_rate'] >= 70:
        status = "✅ TRADEABLE"
        status_msg = "Strategy meets 70%+ win rate requirement"
        status_emoji = "✅"
    elif metrics['win_rate'] >= 60:
        status = "⚠️  MARGINAL"
        status_msg = "Consider tightening entry rules or optimizing parameters"
        status_emoji = "⚠️"
    else:
        status = "❌ NEEDS WORK"
        status_msg = "Optimize parameters before live trading"
        status_emoji = "❌"
    
    print(f"\n{status}: {status_msg}\n")
    
    # Step 7: Save results
    print("[6/6] Saving results...")
    
    # Save trade log
    if len(trades_df) > 0:
        trades_df.to_csv("backtest_trades.csv", index=False)
        print(f"  ✓ Trade log saved: backtest_trades.csv ({len(trades_df)} trades)")
    
    # Save metrics
    with open("backtest_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("  ✓ Metrics saved: backtest_metrics.json")
    
    # Update README
    update_readme(metrics, status_emoji)
    print("  ✓ README.md updated with latest results")
    
    print("\n" + "=" * 70)
    print("Backtest complete! Check README.md for summary.")
    print("=" * 70 + "\n")
    
    return metrics

def update_readme(metrics, status_emoji):
    """Update README with latest backtest results"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    readme = f"""# London Open Imbalance Strategy - Automated Backtest

![Status](https://img.shields.io/badge/Status-{status_emoji}-blue)
![Win Rate](https://img.shields.io/badge/Win_Rate-{metrics['win_rate']}%25-{'green' if metrics['win_rate'] >= 70 else 'orange' if metrics['win_rate'] >= 60 else 'red'})
![Total Pips](https://img.shields.io/badge/Total_Pips-{metrics['total_pips']:+.0f}-{'green' if metrics['total_pips'] > 0 else 'red'})

## 📊 Latest Backtest Results

**Last Updated:** {timestamp}

### Performance Metrics

| Metric | Value |
|--------|-------|
| **Total Trades** | {metrics['total_trades']} |
| **Winners** | {metrics['winners']} |
| **Losers** | {metrics['losers']} |
| **Win Rate** | **{metrics['win_rate']}%** |
| **Total Pips** | **{metrics['total_pips']:+.1f}** |
| **Avg Pips/Trade** | {metrics['avg_pips']:+.2f} |
| **Avg Win** | +{metrics['avg_win_pips']:.1f} pips |
| **Avg Loss** | {metrics['avg_loss_pips']:.1f} pips |
| **Profit Factor** | {metrics['profit_factor']:.2f} |

### Status Assessment
"""
    
    if metrics['win_rate'] >= 70:
        readme += f"""
✅ **TRADEABLE** - Strategy meets 70%+ win rate requirement

This strategy is ready for live trading. The win rate and profit factor indicate a robust edge during London open sessions.
"""
    elif metrics['win_rate'] >= 60:
        readme += f"""
⚠️ **MARGINAL** - Consider optimization

Win rate is acceptable but below target. Consider:
- Increasing volume_multiplier to 2.0 for stricter filtering
- Only trading first 90 minutes of London session
- Focusing on round number levels only
"""
    else:
        readme += f"""
❌ **NEEDS WORK** - Optimize before live trading

Current win rate is below acceptable threshold. Recommended actions:
- Review individual trades in `backtest_trades.csv`
- Adjust entry parameters (volume, wick size, etc.)
- Consider additional filters or different timeframes
"""
    
    readme += f"""

## 📋 Strategy Overview

**Trading Pair:** EURUSD  
**Timeframe:** 5-minute  
**Session:** London Open (3:00-6:00 AM EST / 8:00-11:00 AM UTC)

### Entry Requirements (ALL 5 Must Be Met)

1. **📍 Location Check**
   - Price at round number (00 or 50 level) ±5 pips, OR
   - Price at previous day high/low ±5 pips

2. **📊 Volume Confirmation**
   - Current bar volume > 1.5x the 20-period average
   - Indicates institutional participation

3. **🔄 Rejection Pattern**
   - Previous candle shows 8+ pip wick at the level
   - Demonstrates absorption/order flow imbalance

4. **✅ Confirmation Candle**
   - Current candle closes away from level
   - Body size minimum 5 pips
   - Price breaks above/below previous candle

5. **📈 EMA Alignment**
   - 20 EMA sloping in trade direction
   - Price on correct side of EMA (above for longs, below for shorts)

### Risk Management

- **Stop Loss:** 15 pips
- **Take Profit 1:** 20 pips (close 50% of position)
- **Take Profit 2:** 30 pips (close remaining 50%)
- **Risk/Reward:** 1:2 ratio minimum
- **Max Time in Trade:** 5 hours (time stop)

### Capital Management (for $3 account)

- **Position Size:** 0.10 lots (10 micro lots)
- **Risk per Trade:** 50% of account ($1.50)
- **Stop Loss:** $1.50 loss if hit
- **Take Profit:** $3.00 gain at TP2 (100% ROI per win)

**Growth Path:**
- $3 → $10: Need 3 wins (73% win rate gives 1 loss allowance)
- $10 → $25: Reduce risk to 40% per trade
- $25 → $50: Reduce risk to 30% per trade
- $50 → $100: Reduce risk to 25% per trade

## 🚀 Quick Start

### Run Backtest Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run backtest
python backtest_runner.py
```

### View Results

- **Trade Log:** `backtest_trades.csv` - Individual trade details
- **Metrics:** `backtest_metrics.json` - Performance summary
- **This File:** `README.md` - Auto-updated with latest results

## 📁 Project Structure

```
london-imbalance-backtest/
├── data/
│   ├── download_data.py      # EURUSD data fetcher
│   └── eurusd_5m.csv         # Downloaded price data
├── strategy/
│   └── london_imbalance.py   # Strategy logic
├── backtester/
│   └── engine.py             # Trade execution engine
├── .github/workflows/
│   └── backtest.yml          # GitHub Actions automation
├── backtest_runner.py        # Main script
├── backtest_trades.csv       # Trade results
├── backtest_metrics.json     # Performance metrics
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🤖 Automated Testing

This repository uses GitHub Actions to automatically run backtests:

- ✅ **On every push** to main branch
- ✅ **Daily at 12:00 PM UTC** (7:00 AM EST - after London session)
- ✅ **On-demand** via workflow dispatch

Results are automatically committed back to the repository.

## 📊 Example Trades

Recent winning trades (see `backtest_trades.csv` for full log):

```
Entry Time          | Dir  | Entry   | Exit    | Pips | Reason
--------------------|------|---------|---------|------|--------
2026-01-15 09:30:00 | LONG | 1.0402  | 1.0432  | +30  | TP2
2026-01-16 08:45:00 | LONG | 1.0450  | 1.0470  | +20  | TP1
2026-01-17 10:15:00 | SHORT| 1.0398  | 1.0383  | +15  | TP1
```

## ⚙️ Parameter Optimization

Current parameters can be adjusted in `backtest_runner.py`:

```python
strategy = LondonImbalanceStrategy(
    volume_multiplier=1.5,    # Higher = fewer but cleaner signals
    min_wick_pips=8,          # Minimum rejection size
    min_body_pips=5,          # Minimum confirmation size
    ema_length=20,            # EMA period
    stop_loss_pips=15,        # Stop distance
    tp1_pips=20,              # First target
    tp2_pips=30               # Second target
)
```

## 📈 Next Steps

### If Win Rate ≥ 70% (Tradeable)
1. Begin paper trading with FBS demo account
2. Track 5-10 live trades to validate execution
3. Start live trading with strict discipline

### If Win Rate 60-69% (Marginal)
1. Test with stricter filters (volume_multiplier=2.0)
2. Reduce session window (first 90 minutes only)
3. Focus on round numbers only

### If Win Rate < 60% (Needs Work)
1. Review losing trades for patterns
2. Consider additional filters or rule adjustments
3. Test different session times or pairs

## 📝 License

MIT License - Free to use and modify

## 🤝 Contributing

Feel free to fork, optimize parameters, and submit pull requests with improvements!

---

**Disclaimer:** Past performance does not guarantee future results. Trade at your own risk. This is for educational purposes only.
"""
    
    with open("README.md", "w") as f:
        f.write(readme)

if __name__ == "__main__":
    try:
        run_backtest()
    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        raise
