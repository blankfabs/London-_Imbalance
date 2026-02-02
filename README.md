# London Open Imbalance Strategy - Automated Backtest

Quantitative backtesting system for EURUSD London Open imbalance trading strategy.

## 🚀 Quick Start

### 1. Fork this repository

### 2. Enable GitHub Actions
- Go to **Actions** tab in your fork
- Click "I understand my workflows, go ahead and enable them"

### 3. Run first backtest
- Go to **Actions** → **Daily Backtest** → **Run workflow**
- Wait 2-3 minutes for completion
- Check updated README for results

## 📊 Strategy Overview

**Pair:** EURUSD  
**Timeframe:** 5-minute  
**Session:** London Open (3:00-6:00 AM EST)

### Entry Rules (ALL 5 required)

1. Price at key level (round number or previous day H/L)
2. Volume spike (>1.5x average)
3. Rejection pattern (8+ pip wick)
4. Confirmation candle (5+ pip body, closes away from level)
5. EMA alignment (20 EMA trending with trade)

### Risk Parameters

- Stop Loss: 15 pips
- Take Profit 1: 20 pips
- Take Profit 2: 30 pips

## 💻 Run Locally

```bash
pip install -r requirements.txt
python backtest_runner.py
```

## 📁 Files

- `backtest_runner.py` - Main script
- `strategy/london_imbalance.py` - Strategy logic
- `backtester/engine.py` - Trade execution
- `data/download_data.py` - Data fetcher
- `.github/workflows/backtest.yml` - Automation

## 🤖 Automation

Backtests run automatically:
- On every push to main
- Daily at 12:00 PM UTC (7:00 AM EST)
- On-demand via Actions tab

Results auto-commit to this README.

## 📈 Target Performance

- **Win Rate:** ≥70%
- **Profit Factor:** ≥2.0
- **Average Win:** >20 pips

## 📝 License

MIT - Free to use and modify

---

**Note:** First backtest run will populate this README with actual results.
