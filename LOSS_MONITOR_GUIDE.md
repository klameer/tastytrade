# Loss Monitor - Stop Loss Advisor

## ✅ Yes! The System WILL Advise on Early Exits

Your system now **actively monitors losing positions** and recommends when to cut losses.

---

## 🎯 What It Does

### Automatic Position Health Checks

Every time you run `daily_routine.py`, the system:
1. ✅ Checks all open positions
2. ✅ Calculates unrealized P&L
3. ✅ Compares losses to thresholds
4. ✅ **Recommends exits** for positions going against you

---

## 🚨 Three Severity Levels

### CRITICAL (Exit Immediately)
- Loss > 100% of credit received (2x max loss)
- **Action**: 🚨 EXIT TODAY
- **Why**: Position has exceeded acceptable loss threshold
- **Example**: Sold $2 credit spread, now worth $4 (losing $2 = 100% loss)

### WARNING (Exit Soon)
- Loss > 50% but < 100%
- **Action**: ⚠️ EXIT WITHIN 1-2 DAYS
- **Why**: Significant unrealized loss
- **Example**: Sold $2 credit spread, now worth $3 (losing $1 = 50% loss)

### WATCH (Monitor Closely)
- Loss > 25% but < 50%
- **Action**: 📊 MONITOR, SET MENTAL STOP AT -50%
- **Why**: Moderate loss, could recover
- **Example**: Sold $2 credit spread, now worth $2.50 (losing $0.50 = 25% loss)

---

## 📊 Example Output

```
STEP 3: LOSS MONITOR - POSITION HEALTH CHECK
================================================================================

⚠️  ALERT: 3 position(s) need attention!

--------------------------------------------------------------------------------

🚨 CRITICAL: SPY 260220P00565000
  Position:     7 contracts
  Current P&L:  $-2,450.00 (-105.7%)
  Current:      $2.75
  Entry:        $1.85

  ACTION: 🚨 EXIT IMMEDIATELY
  REASON: Loss exceeds 2x max acceptable loss
  EXECUTE: Close this position today

--------------------------------------------------------------------------------

⚠️  WARNING: NVDA 260120P00130000
  Position:     3 contracts
  Current P&L:  $-675.00 (-64.3%)
  Current:      $3.00
  Entry:        $1.75

  ACTION: ⚠️  STRONGLY CONSIDER EXITING
  REASON: Significant unrealized loss (>50%)
  EXECUTE: Exit within 1-2 days or set hard stop

--------------------------------------------------------------------------------

📊 WATCH: QQQ 260213P00480000
  Position:     5 contracts
  Current P&L:  $-325.00 (-37.1%)
  Current:      $2.40
  Entry:        $1.75

  ACTION: 📊 MONITOR CLOSELY
  REASON: Moderate loss - watch for further deterioration
  EXECUTE: Set mental stop at -50%

--------------------------------------------------------------------------------
```

---

## 🎓 Stop Loss Rules (Configurable)

Default thresholds in `loss_monitor.py`:

```python
'max_loss_pct': 100,      # Exit if loss > 100% of credit
'max_loss_multiple': 2.0,  # Exit if loss > 2x credit received
'time_stop_days': 21,      # Exit if losing after 21 days (75% of 30 DTE)
'delta_warning': 0.50,     # Warn if delta moves significantly
```

### Why These Thresholds?

**2x Max Loss Rule:**
- If you sold a $5 wide spread for $1.75 credit:
  - Max possible loss = $5 - $1.75 = $3.25
  - Exit threshold = $1.75 × 2 = $3.50 (more than max!)
- This forces you out before max loss hits

**Time Stop:**
- If you're losing after 21 days (75% timeframe)
- Theta decay isn't helping
- Time to admit you're wrong

---

## 💡 Why This Matters

### Without Loss Monitor:

```
Day 1:  "It's down $200, no big deal"
Day 5:  "It's down $800, might come back"
Day 10: "It's down $2,000, too late to exit now"
Result: Max loss → -$3,250
```

### With Loss Monitor:

```
Day 1:  "It's down $200" → 📊 WATCH
Day 5:  "It's down $875" → ⚠️  WARNING - Exit soon
Day 6:  Exit at $900 loss → Saved $2,350!
```

---

## 🎯 Philosophy: Cut Losers Quickly

### The Tastytrade Way

1. **Winners take care of themselves** (50% rule)
2. **Losers need hard stops** (don't hope)
3. **Small losses are OK** (cost of doing business)
4. **Big losses destroy accounts** (MUST avoid)

### Real Numbers

If you:
- Win 65% of trades at 35% return
- Lose 35% of trades at -50% return
→ **Profitable!** (+12.7% overall)

But if you:
- Win 65% at 35%
- Lose 35% at **-150%** (no stops)
→ **Losing!** (-29.5% overall)

**Stop losses are not optional.**

---

## 🔧 How to Use

### Daily Workflow

```powershell
# Run daily routine
.venv\Scripts\activate.ps1 ; python daily_routine.py
```

Step 3 will show:
```
STEP 3: LOSS MONITOR - POSITION HEALTH CHECK
```

If you have losing positions:
```
🚨 CRITICAL: YOU HAVE POSITIONS THAT NEED IMMEDIATE EXITS!

EXIT RECOMMENDATIONS
================================================================================

🚨 CRITICAL - EXIT TODAY:
SPY             | Loss: $-2,450.00 (-105.7%)
                | Action: Close immediately - loss too large

⚠️  WARNING - EXIT SOON:
NVDA            | Loss: $   -675.00 ( -64.3%)
                | Action: Exit within 1-2 days

📊 WATCH - MONITOR:
QQQ             | Loss: $   -325.00 ( -37.1%)
                | Action: Set stop at -50%

GENERAL RULES:
  • Cut losers quickly - don't let hope turn into disaster
  • Accept small losses to preserve capital
  • Never let a winner turn into a loser
  • Remember: You can always re-enter if thesis still valid
```

### Stand-Alone Check

```powershell
# Check losses anytime
python loss_monitor.py
```

---

## ⚙️ Customizing Thresholds

Edit `loss_monitor.py`:

```python
# More aggressive (tighter stops)
self.rules = {
    'max_loss_pct': 50,       # Exit at 50% loss
    'max_loss_multiple': 1.5,  # Exit at 1.5x credit
}

# More conservative (wider stops)
self.rules = {
    'max_loss_pct': 150,      # Exit at 150% loss
    'max_loss_multiple': 2.5,  # Exit at 2.5x credit
}
```

**Recommendation**: Start with defaults, adjust based on YOUR trading style.

---

## 🚫 What Won't Work

### "I'll just hold it"
- Hope is not a strategy
- Losers rarely come back
- Opportunity cost (capital tied up)

### "But it might recover"
- Small chance × big loss = bad math
- Even if 30% recover, 70% don't
- Cut losses, redeploy capital

### "I don't want to realize the loss"
- Unrealized loss = realized loss
- Your P&L doesn't care about your feelings
- Take the loss, move on

---

## ✅ Daily Routine Updated

Your `daily_routine.py` now includes 6 steps:

1. **Update Earnings Calendar**
2. **Check Positions for Earnings**
3. **Loss Monitor** ← NEW!
4. **Auto-Detect Trade Changes**
5. **Performance Analysis**
6. **Scan for New Opportunities**

**Critical exits flagged at the top of summary!**

---

## 📈 Expected Impact

### After Implementing Stop Losses

**Before:**
- Occasional huge losers (-150%, -200%)
- Wipes out 3-5 winners
- Emotional damage
- "Why do I keep doing this?"

**After:**
- Max loss capped at -100%
- Preserve capital
- Less stress
- Consistent results

**Real example:**
- 10 trades: 7 wins (+$3,500), 3 losses (-$2,400) = **+$1,100 profit**
- WITHOUT stops: 7 wins (+$3,500), 3 disasters (-$6,000) = **-$2,500 loss**

**Stop losses = difference between profitable and broke.**

---

## 🎯 Remember

1. The system will TELL you when to exit
2. You have to LISTEN and execute
3. Cutting losers is HARD emotionally
4. Following rules is EASIER with automation
5. Small losses = staying alive to trade tomorrow

Your system now protects you from yourself. Use it! 🛡️
