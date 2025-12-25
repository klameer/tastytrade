# Trade Memory & Learning System

## Overview

The trade journal system tracks every recommendation, execution, and outcome to create a learning feedback loop that improves future trading decisions.

## System Components

### 1. Trade Journal Database (`trade_journal.py`)

SQLite database with 4 tables:

**Recommendations Table**
- Every scanner recommendation is logged
- Includes: symbol, strategy, strikes, expected outcomes, IV rank, recommended contracts
- Status: `recommended` → `executed` or `ignored`

**Trades Table**
- Actual trades you execute
- Links to recommendation that triggered it
- Tracks: entry date, actual contracts, entry credit, exit details, P&L
- Status: `open` → `closed`

**Performance Metrics Table**
- Calculated statistics: win rate, profit factor, avg winner/loser
- Updated after each trade closes
- Time-series tracking of performance

**Insights Table**
- Auto-generated learnings from each trade
- Examples:
  - "High IV rank (68%) contributed to success"
  - "Low IV rank (35%) may have caused failure"
  - "Followed 50% rule: closed at 52% of max profit"

### 2. Position Tracker (`position_tracker.py`)

**Automatic Syncing**:
- Fetches current positions from tastytrade API
- Compares with open journal entries
- Detects when positions close → auto-logs exits
- No manual tracking needed!

**Benefits**:
- Never forget to log a trade
- Automatically tracks P&L
- Triggers analysis when trades close

### 3. Learning System (`learning_system.py`)

**Analyzes patterns** in closed trades:

```python
# What it learns:
- Optimal IV rank threshold (winners vs losers)
- Best DTE range for your style
- Which symbols work best for you
- Which close reasons yield best results
- Win rate by strategy type
```

**Auto-adjusts scanner**:
- If win rate < 50% → Increase IV rank threshold
- If win rate > 70% → More aggressive (lower threshold, more opportunities)
- Blacklist underperforming symbols
- Favor symbols with proven track record

### 4. Weekly Reports

Automatic performance summaries:
- Trades closed this week
- Total P&L
- Key insights discovered
- Parameter adjustment recommendations

## Usage Workflow

### When Scanner Finds Opportunity

```python
from options_scanner import OptionsScanner
from position_sizer import PositionSizer
from trade_journal import TradeJournal

scanner = OptionsScanner()
sizer = PositionSizer(account_size=46000)
journal = TradeJournal()

# Run scan
opportunities = scanner.scan_for_opportunities()

# For each opportunity
for opp in opportunities:
    sizing = sizer.calculate_position_details(opp)
    
    # LOG THE RECOMMENDATION
    rec_id = journal.log_recommendation(opp, sizing, 
                                       reason="Scanner auto-generated")
```

### When You Enter Trade

```python
# You executed the trade in tastytrade
# Log it in the journal:

journal.log_trade_entry(
    rec_id=1,              # From scanner recommendation
    actual_contracts=7,     # What you actually entered
    entry_credit=1.90,      # Actual fill price
    iv_rank=68.5,          # IV at entry
    notes="Entered at better price than expected"
)
```

### When Trade Closes

```python
# Manual logging:
journal.log_trade_exit(
    trade_id=1,
    exit_debit=0.95,       # What you paid to close
    close_reason="50% profit rule",
    notes="Closed in 12 days for $665 profit"
)

# This automatically:
# 1. Calculates P&L
# 2. Analyzes why it worked/failed
# 3. Stores insights
# 4. Updates performance metrics
```

### Weekly Review

```python
from learning_system import TradeLearningSystem

learner = TradeLearningSystem()

# See what's working
learner.analyze_what_works()

# Get recommendations
learner.generate_weekly_report()
```

## Example Learning Flow

### After 10 closed trades:

```
LEARNING ANALYSIS: What Works?
================================================================================

IV RANK ANALYSIS:
  Winners avg IV:  65.3%
  Losers avg IV:   42.1%
  💡 INSIGHT: Higher IV rank (65.3%) correlates with wins
  → RECOMMENDATION: Increase min_iv_rank threshold to 60%

DTE ANALYSIS:
  Winners avg DTE: 45 days
  Losers avg DTE:  35 days

SYMBOL PERFORMANCE (2+ trades):
  SPY    - 4 trades, 75% win rate, Avg P&L: $520.00
  QQQ    - 3 trades, 67% win rate, Avg P&L: $385.00
  NVDA   - 2 trades, 50% win rate, Avg P&L: $120.00

CLOSE REASONS:
  50% profit rule: 5 trades, Avg P&L: $475.00
  Stop loss: 3 trades, Avg P&L: -$280.00

PARAMETER RECOMMENDATIONS
================================================================================
✓ Excellent win rate (70%) - Consider:
  - Lower min_iv_rank to 40% (find more opportunities)
  - Focus on SPY and QQQ (proven winners)
  - Continue following 50% profit rule
```

### Scanner Auto-Adjusts:

```python
# Next time scanner runs, it uses learned parameters:
scanner = OptionsScanner(
    min_iv_rank=60,  # Increased based on learning
    target_dte=45     # Optimized from historical data
)

# Prioritizes symbols with best track record
# Adjusts strike selection based on what worked
```

## Data Persistence

**Everything stored in SQLite database**: `trade_journal.db`

You can:
- Query it directly with SQL
- Export to Excel/CSV
- Back up regularly
- Carry learning across conversations

**Location**: Project directory
**Backup**: Automatically included in project backups

## Benefits

1. **Never Lose Track** - All trades logged automatically
2. **Objective Analysis** - Data-driven insights, not emotions
3. **Continuous Improvement** - Scanner gets smarter over time
4. **Pattern Recognition** - Identifies what works for YOUR style
5. **Accountability** - Complete audit trail of decisions
6. **Performance Tracking** - Real-time win rate, profit factor, etc.

## Integration with Scanner

The updated scanner now:
1. Logs every recommendation to journal
2. Checks historical performance before suggesting symbols
3. Adjusts parameters based on your actual results
4. Shows past performance with each symbol

## Future Enhancements

Potential additions:
- Auto-sync with tastytrade (detect entries/exits automatically)
- Email/SMS alerts when trades reach 50% profit
- ML model to predict trade success probability
- Correlation analysis (avoid too many correlated positions)
- Greeks portfolio tracking
- Tax lot optimization

## Files

| File | Purpose |
|------|---------|
| `trade_journal.py` | Core database and logging |
| `position_tracker.py` | Auto-sync with tastytrade |
| `learning_system.py` | Analysis and recommendations |

## Getting Started

Markets are closed now, but when they open:

```powershell
# 1. Run scanner (auto-logs recommendations)
.venv\Scripts\activate.ps1 ; python generate_recommendations.py

# 2. Enter trades in tastytrade

# 3. Log your entries
python -c "from trade_journal import TradeJournal; j = TradeJournal(); j.log_trade_entry(...)"

# 4. Trades close automatically or log manually

# 5. Weekly review
python learning_system.py
```

The system learns from every trade, making you a better trader over time!
