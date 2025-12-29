# Earnings Calendar Integration - Complete

## ✅ What Was Added

### 1. **Earnings Calendar System** (`earnings_calendar.py`)

Automatically tracks earnings dates for all watchlist symbols:

**Features:**
- Fetches earnings dates from Yahoo Finance API
- Stores dates in SQLite database
- Checks if symbols have upcoming earnings
- Displays earnings calendar for next 14 days
- Warns about positions with upcoming earnings

### 2. **Scanner Integration**

Options scanner now filters out stocks with upcoming earnings:

```python
scanner = OptionsScanner(
    avoid_earnings=True,  # Default: filters earnings
    earnings_window_days=7  # Avoids stocks with earnings in next 7 days
)
```

**What It Does:**
- Checks each high-IV candidate for earnings
- Filters them out before analyzing option chains
- Shows which symbols were filtered
- Saves time by not analyzing earnings plays

### 3. **Daily Routine Integration**

Your `daily_routine.py` now includes:

**Step 1: Update Earnings Calendar**
- Updates earnings dates weekly (to avoid rate limits)
- Shows upcoming earnings for next 14 days
- Color-coded warnings (imminent, soon, upcoming)

**Step 2: Check Positions for Earnings**
- Scans your open positions
- Warns if any have earnings in next 14 days
- Suggests action (exit or roll)

## 🎯 How It Works

### Scanner Example

```
OPTIONS SCANNER
================================================================================
Scanning 20 symbols...
Criteria: IV Rank > 50%, DTE: ~45 days

✓ Found 8 symbols with IV Rank > 50%

📅 Checking for earnings in next 7 days...

  ⚠️  Filtered out 3 symbols with upcoming earnings:
    AAPL   - Earnings in 4 days (2026-01-15)
    NVDA   - Earnings in 6 days (2026-01-17)
    MSFT   - Earnings in 7 days (2026-01-18)

✓ 5 symbols after earnings filter

Top Candidates:
  SPY    - IV Rank: 68.5%
  QQQ    - IV Rank: 65.2%
  ...
```

### Position Warning Example

```
CHECKING POSITIONS FOR EARNINGS
================================================================================

  ⚠️  ALERT: 2 position(s) have upcoming earnings!
------------------------------------------------------------

  ORCL     - Earnings in 5 days (2026-01-20)
    Position: 200 shares
    Action: Consider exiting before earnings or rolling to later date

  NVDA     - Earnings in 3 days (2026-01-18)
    Position: 3 contracts
    Action: Consider exiting before earnings or rolling to later date
```

## 📅 Earnings Calendar Display

```
EARNINGS IN NEXT 14 DAYS
------------------------------------------------------------
Symbol   Date         Days Until      Action
------------------------------------------------------------
AAPL     2026-01-15   2 days         ⚠️  IMMINENT - Avoid
MSFT     2026-01-17   4 days         ⚡ Soon - Consider exit
NVDA     2026-01-20   7 days         📊 Upcoming - Monitor
TSLA     2026-01-25   12 days        📊 Upcoming - Monitor
------------------------------------------------------------
```

## ⚙️ Configuration

### Avoid Earnings (Default)

```python
# Scanner automatically filters earnings
scanner = OptionsScanner(avoid_earnings=True)
```

**Why:** Earnings create unpredictable volatility. Even if IV is high, the stock can gap past your strikes.

### Trade Earnings (Advanced)

```python
# Explicitly trade IV crush after earnings
scanner = OptionsScanner(
    avoid_earnings=False  # Don't filter
)
```

**Strategy:** Sell premium right before earnings, close next day after volatility crushes. **High risk!**

### Adjust Warning Window

```python
# Check for earnings further out
scanner = OptionsScanner(
    avoid_earnings=True,
    earnings_window_days=14  # Avoid earnings 2 weeks out
)
```

## 🔄 Daily Workflow

```powershell
# Run daily routine
.venv\Scripts\activate.ps1 ; python daily_routine.py
```

Automatic steps:
1. ✅ Updates earnings calendar (weekly)
2. ✅ Shows upcoming earnings
3. ✅ Warns about positions with earnings
4. ✅ Filters earnings from scanner
5. ✅ Finds safe opportunities

## 💾 Data Storage

Earnings stored in `trade_journal.db`:

```sql
-- View all upcoming earnings
SELECT symbol, earnings_date 
FROM earnings_calendar 
WHERE DATE(earnings_date) >= DATE('now')
ORDER BY earnings_date;

-- Check specific symbol
SELECT * FROM earnings_calendar WHERE symbol = 'AAPL';
```

## 🎓 Best Practices

### 1. **Avoid Earnings by Default**
Unless you're specifically trading IV crush, filter out earnings:
- Less surprise gaps
- More predictable outcomes
- Better fit for high-probability strategies

### 2. **Exit Before Earnings**
If you hold a position and earnings approaches:
- Exit 2-3 days before earnings
- Roll to next month
- Or accept the risk (not recommended)

### 3. **IV Crush Strategy** (Advanced)
If you DO want to trade earnings:
- Sell premium day before earnings
- Close next morning (don't hold)
- Use small position sizes
- Accept high risk

### 4. **Weekly Updates**
Calendar updates weekly automatically to avoid rate limits:
- Yahoo Finance allows ~2000 requests/hour
- 84 symbols = minimal impact
- Updates Sunday night ready for Monday

## 📊 Example Trade Decision

**Scenario:** Scanner finds NVDA with 72% IV rank

**Without Earnings Filter:**
```
"NVDA looks great! 72% IV rank, let's sell puts"
→ Earnings in 3 days
→ Stock gaps down 8% after earnings
→ Your puts are ITM → Loss
```

**With Earnings Filter (Default):**
```
"NVDA has 72% IV rank BUT earnings in 3 days"
→ Filtered out automatically
→ Scanner shows SPY instead (no earnings)
→ Trade SPY safely
```

## 🚀 Updates Made

- ✅ Added `yfinance` to requirements
- ✅ Created `earnings_calendar.py`
- ✅ Integrated into `options_scanner.py`
- ✅ Added to `daily_routine.py`
- ✅ Auto-updates weekly
- ✅ Warns about position earnings

## 🎯 Next Steps

When markets open:
1. Run `python daily_routine.py`
2. See upcoming earnings
3. Get warnings about your positions
4. Scanner automatically avoids earnings stocks
5. Trade safely!

Your system now protects you from earnings surprises! 🎉
