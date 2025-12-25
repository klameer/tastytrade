# Tastytrade AI Trading System

Complete automated trading system for high-probability options trading with automatic trade tracking and learning.

## 🎯 What This System Does

1. **Scans 84+ stocks** daily for high-probability options trades
2. **Automatically detects** when you enter/exit trades (no manual logging!)
3. **Learns from your results** and adjusts parameters
4. **Recommends optimal position sizing** (5% max risk per trade)
5. **Tracks performance** with win rate, profit factor, etc.

## 🚀 Quick Start

### Daily Workflow (Once Markets Open)

```powershell
# Run this ONCE per day
.venv\Scripts\activate.ps1 ; python daily_routine.py
```

This single command:
- Detects any trades you entered/exited
- Logs them automatically to journal
- Analyzes your performance
- Finds new opportunities
- Generates trade recommendations

**That's it!** No manual tracking needed.

## 📁 Key Files

| File | Purpose |
|------|---------|
| `daily_routine.py` | **Run this daily** - complete workflow |
| `auto_trade_detector.py` | Auto-detects trades from portfolio |
| `options_scanner.py` | Finds high-probability setups |
| `trade_journal.py` | Tracks all trades and performance |
| `learning_system.py` | Learns what works for you |
| `watchlist.py` | 84 symbols across all sectors |
| `position_sizer.py` | Calculates optimal contract quantities |

## 📊 How Auto-Detection Works

### First Run (Takes Snapshot)
```
python auto_trade_detector.py
→ Takes snapshot of your current positions
→ "Need 2 snapshots to detect changes"
```

### Second Run (Detects Changes)
```
python auto_trade_detector.py

✅ NEW POSITIONS DETECTED (2):
  + SPY 260220P00565000 | 7 contracts @ $1.90
    → Auto-logged to trade journal!
  
❌ CLOSED POSITIONS DETECTED (1):
  - NVDA 260120P00130000 | 3 contracts
    → Exit logged with +$285 profit!
```

**Zero manual work!** System detects everything automatically.

## 🧠 Learning System

After 10+ trades, the system tells you:
```
LEARNING ANALYSIS: What Works?
================================================================================

IV RANK ANALYSIS:
  Winners avg IV:  65.3%
  Losers avg IV:   42.1%
  💡 INSIGHT: Higher IV rank correlates with wins
  → RECOMMENDATION: Increase min_iv_rank to 60%

SYMBOL PERFORMANCE:
  SPY  - 4 trades, 75% win rate, Avg P&L: $520
  QQQ - 3 trades, 67% win rate, Avg P&L: $385

PARAMETER RECOMMENDATIONS:
  ✓ Excellent win rate (70%)
  → Lower min_iv_rank to find more opportunities
  → Continue following 50% profit rule
```

The scanner **automatically adjusts** based on YOUR results!

## 📈 Portfolio Analysis

```powershell
# Analyze current portfolio
python analyze_portfolio.py

# Calculate exit proceeds
python portfolio_exit_plan.py
```

Your current portfolio:
- **Net Value**: $26,252.68
- **Positions**: 10 (5 equities + 5 options)
- **Exit Plan**: ~$46K available after liquidation
- **Recommended**: Exit all and start fresh with scanner

## 🎓 Trading Strategy

### Current Approach (Needs Fixing)
- ✗ Directional long calls only
- ✗ No diversification (ORCL = 150% of portfolio)
- ✗ No risk management
- ✗ 70% losing positions

### New Approach (Scanner Recommends)
- ✓ High-probability credit spreads (50-70% win rate)
- ✓ Diversified across 6-8 positions
- ✓ Strict position sizing (5% max risk)
- ✓ Only trade when IV rank > 50%
- ✓ Close winners at 50% profit

### Tastytrade Methodology
1. **Sell premium when IV rank > 50%**
2. **30-45 DTE** for optimal theta decay
3. **~0.30 delta strikes** (70% probability OTM)
4. **1/3 credit target** (credit ≥ spread width / 3)
5. **50% profit exits** reduce reversal risk

## 🔧 Installation

Already installed! Everything is in your virtual environment:
```powershell
.venv\Scripts\activate.ps1
```

## 📚 Documentation

- `AUTO_DETECTION_GUIDE.md` - How automatic detection works
- `TRADE_MEMORY_SYSTEM.md` - Learning system details
- `walkthrough.md` - Complete implementation walkthrough

## 🎯 Next Steps (When Markets Open)

### 1. Exit Current Portfolio (Optional)
```powershell
# See exit plan
python portfolio_exit_plan.py

# Then manually exit positions in tastytrade
# Expected proceeds: ~$46,000
```

### 2. Run First Snapshot
```powershell
python auto_trade_detector.py
# Takes first snapshot of current positions
```

### 3. Daily Routine
Every trading day:
```powershell
python daily_routine.py
```

This becomes your complete workflow!

### 4. Enter Recommended Trades
- Review recommendations from scanner
- Enter trades you like in tastytrade
- Next day, system auto-detects them

### 5. Monitor & Learn
After 10+ trades:
```powershell
python learning_system.py
# See what's working for you
# Scanner adjusts automatically
```

## 💾 Data Storage

Everything stored in `/trade_journal.db`:
- All recommendations made
- Trades executed (auto-detected)
- Performance metrics
- Learning insights
- Position snapshots

**Backup regularly!** This is your trading memory.

## 🔒 Security

Credentials stored in `.env`:
```
TASTYTRADE_CLIENT_SECRET=your_secret_here
TASTYTRADE_REFRESH_TOKEN=your_token_here
```

Never commit `.env` to git (already in `.gitignore`)

## 📞 Support

All code is documented and ready to use. When markets open:

1. Run `python daily_routine.py` once per day
2. Review trade recommendations
3. Enter trades you like in tastytrade
4. System handles the rest automatically!

## 🎁 What You Built Today

- ✅ Complete tastytrade API client
- ✅ Portfolio analyzer
- ✅ Exit plan calculator
- ✅ Options scanner (84+ symbols)
- ✅ Position sizing calculator
- ✅ **Automatic trade detector** (NEW!)
- ✅ Trade journal with SQLite database
- ✅ Learning system that improves over time
- ✅ Daily routine automation

**Total automation**: Just enter trades in tastytrade, run one script daily, and the system learns from your actual results!

Merry Christmas! 🎄 Happy trading when markets open! 📈
