# Automatic Trade Detection - How It Works

## No More Manual Logging!

The system now **automatically detects** when you enter or exit trades by comparing your portfolio positions.

## How It Works

### 1. Position Snapshots

Every time you run the detector, it:
1. Fetches your current positions from tastytrade
2. Saves a snapshot to the database
3. Compares with the previous snapshot
4. Detects what changed

### 2. Change Detection

**New Positions (Entries)**
```
Last Snapshot:  SPY $565 Put (0 contracts)
Current:        SPY $565 Put (7 contracts)
→ DETECTED: You entered 7 contracts
→ AUTO-LOGS: Entry to trade journal
```

**Closed Positions (Exits)**
```
Last Snapshot:  QQQ $480 Put (5 contracts)
Current:        QQQ $480 Put (0 contracts)
→ DETECTED: Position closed
→ AUTO-LOGS: Exit with realized P&L
```

**Quantity Changes (Partial closes/adds)**
```
Last Snapshot:  NVDA $130 Put (10 contracts)
Current:        NVDA $130 Put (5 contracts)
→ DETECTED: Reduced by 5 contracts
```

### 3. Automatic Matching

When a new position is detected:
1. System looks for matching recommendation from last 7 days
2. If found → links trade to recommendation
3. Logs entry with all details automatically

When a position closes:
1. System finds the open trade in journal
2. Calculates P&L automatically
3. Logs exit and triggers analysis

## Daily Workflow

### Simple! Just run once per day:

```powershell
.venv\Scripts\activate.ps1 ; python daily_routine.py
```

This automatically:
1. ✓ Detects any trades you entered since yesterday
2. ✓ Detects any positions you closed
3. ✓ Logs everything to trade journal
4. ✓ Runs performance analysis (if enough trades)
5. ✓ Finds new opportunities
6. ✓ Generates recommendations

**You don't touch the journal manually at all!**

## What Gets Logged Automatically

### Entry Detection
- Trade symbol and strategy
- Number of contracts
- Entry price (from avg cost basis)
- Current IV rank
- Links to scanner recommendation (if exists)

### Exit Detection
- Exit date
- Realized P&L
- Days held
- Close reason (auto-detected or expired)

### Example Output

```
AUTO-DETECTING TRADES - Account 5WZ85685
================================================================================

📊 POSITION CHANGES SINCE 2025-12-24

✅ NEW POSITIONS DETECTED (2):
  + SPY 260220P00565000    | Equity Option   | Qty:     7.00 | Avg Price: $1.90
    → Auto-logged to trade journal (Trade #15, Rec #12)
  
  + QQQ 260213P00480000    | Equity Option   | Qty:     5.00 | Avg Price: $1.75
    → Auto-logged to trade journal (Trade #16, Rec #13)

❌ CLOSED POSITIONS DETECTED (1):
  - NVDA 260120P00130000   | Equity Option   | Qty:     3.00
    → Auto-logged exit to trade journal (Trade #14)
    → Realized P&L: +$285.00 (Winner!)

🔄 QUANTITY CHANGES DETECTED (0):
  No partial position changes

📸 Taking position snapshot for account 5WZ85685...
  ✓ Snapshot saved: 15 positions
```

## First Time Setup

**Run 1 (Today):**
```
⚠️  Need at least 2 snapshots to detect changes.
   Taking first snapshot now...
   
📸 Taking position snapshot...
  ✓ Snapshot saved: 10 positions
```

**Run 2 (Tomorrow):**
```
✅ NEW POSITIONS DETECTED (2):
  + SPY $565 Put | 7 contracts
    → Auto-logged!
```

After first snapshot, every subsequent run detects changes!

## Benefits

### ✅ Zero Manual Work
- No copy/pasting trade details
- No forgetting to log trades
- No manual P&L calculations

### ✅ Perfect Accuracy
- Gets data directly from tastytrade
- Exact entry/exit prices
- Real P&L from actual fills

### ✅ Complete History
- Every trade logged automatically
- Full audit trail
- Learning system has all data

### ✅ Real-Time Insights
- See what you actually traded
- Compare to scanner recommendations
- Learn from execution vs plan

## Advanced: Custom Schedules

You can run as often as you want:

**Multiple times per day:**
```powershell
# Run every hour during market hours
# Each run takes a new snapshot and detects changes
python auto_trade_detector.py
```

**Once per day (recommended):**
```powershell
# End of trading day
python daily_routine.py
```

**After entering trades:**
```powershell
# Immediately after placing trades
python auto_trade_detector.py
# Detects your new positions right away
```

## How Positions Are Identified

Each position gets a unique hash based on:
- Symbol (including expiration + strike for options)
- Instrument type

This ensures:
- Same position = same hash
- Different positions = different hashes
- No false positives

## Data Storage

Position snapshots stored in `trade_journal.db`:
```sql
-- View all snapshots
SELECT * FROM position_snapshots
ORDER BY snapshot_date DESC;

-- See what changed today
SELECT * FROM position_snapshots
WHERE DATE(snapshot_date) = DATE('now');
```

## Summary

**Old way:**
1. Enter trade in tastytrade
2. Manually write down details
3. Log to journal
4. Calculate P&L when closing
5. Hope you didn't forget anything

**New way:**
1. Enter trade in tastytrade
2. Run `python daily_routine.py` once per day
3. Done! Everything auto-tracked

The system learns from your ACTUAL trades, not what you PLANNED to trade!
