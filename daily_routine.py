"""
Daily Trading Routine
Run this once per day to:
1. Detect new trades automatically
2. Find new opportunities
3. Generate recommendations
"""

from auto_trade_detector import AutoTradeDetector
from generate_recommendations import run_full_scan_and_recommend
from learning_system import TradeLearningSystem
from datetime import datetime
import sys
import os
from pathlib import Path


class OutputCapture:
    """Capture output to both console and file."""
    
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log = open(filepath, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        # Remove ANSI color codes for markdown
        import re
        clean_message = re.sub(r'\x1b\[[0-9;]*m', '', message)
        self.log.write(clean_message)
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()


def daily_routine():
    """Complete daily trading routine."""
    
    print("="*80)
    print("TASTYTRADE DAILY ROUTINE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Step 1: Update Earnings Calendar
    print("\n" + "="*80)
    print("STEP 1: UPDATING EARNINGS CALENDAR")
    print("="*80)
    
    from earnings_calendar import EarningsCalendar, check_positions_for_earnings
    from watchlist import get_full_watchlist
    from tastytrade_client import TastytradeClient
    
    calendar = EarningsCalendar()
    watchlist = get_full_watchlist()
    
    # Update earnings for watchlist (do this weekly to avoid rate limits)
    import os
    update_file = "last_earnings_update.txt"
    should_update = True
    
    if os.path.exists(update_file):
        with open(update_file, 'r') as f:
            last_update = f.read().strip()
            from datetime import timedelta
            last_date = datetime.fromisoformat(last_update)
            if (datetime.now() - last_date).days < 7:
                should_update = False
                print(f"\n  ℹ️  Earnings last updated {(datetime.now() - last_date).days} days ago - skipping update")
    
    if should_update:
        print(f"\n  Updating earnings calendar...")
        calendar.update_earnings(watchlist)
        with open(update_file, 'w') as f:
            f.write(datetime.now().isoformat())
    
    # Show upcoming earnings
    calendar.display_upcoming_earnings(14)
    
    # Step 2: Check positions for earnings warnings
    print("\n" + "="*80)
    print("STEP 2: CHECKING POSITIONS FOR EARNINGS")
    print("="*80)
    
    client = TastytradeClient()
    accounts = client.get_account_numbers()
    
    if accounts:
        positions = client.get_positions(accounts[0])
        
        if positions:
            warnings = check_positions_for_earnings(calendar, positions)
            
            if warnings:
                print(f"\n  ⚠️  ALERT: {len(warnings)} position(s) have upcoming earnings!")
                print("-" * 60)
                for warning in warnings:
                    pos = warning['position']
                    earnings_info = warning['earnings_info']
                    print(f"\n  {earnings_info['symbol']:8} - Earnings in {earnings_info['days_until']} days ({earnings_info['earnings_date']})")
                    print(f"    Position: {pos.get('quantity')} contracts")
                    print(f"    Action: Consider exiting before earnings or rolling to later date")
            else:
                print(f"\n  ✓ No positions have earnings in next 14 days")
        else:
            print(f"\n  ℹ️  No open positions")
    
    # Step 3: Check for losing positions that need exits
    print("\n" + "="*80)
    print("STEP 3: LOSS MONITOR - POSITION HEALTH CHECK")
    print("="*80)
    
    from loss_monitor import LossMonitor
    
    monitor = LossMonitor()
    
    if accounts:
        loss_results = monitor.check_positions(accounts[0])
        
        # If there are critical warnings, display exit report
        if loss_results['warnings']:
            critical = [w for w in loss_results['warnings'] if w['severity'] == 'CRITICAL']
            if critical:
                print("\n" + "!"*80)
                print("🚨 CRITICAL: YOU HAVE POSITIONS THAT NEED IMMEDIATE EXITS!")
                print("!"*80)
                print(monitor.generate_exit_report(loss_results['warnings']))
    
    # Step 4: Detect trade changes
    print("\n" + "="*80)
    print("STEP 4: AUTO-DETECTING TRADE CHANGES")
    print("="*80)
    
    detector = AutoTradeDetector()
    
    for account in accounts:
        detector.detect_changes(account)
    
    # Step 5: Check if we should run learning analysis
    print("\n" + "="*80)
    print("STEP 5: PERFORMANCE ANALYSIS")
    print("="*80)
    
    learner = TradeLearningSystem()
    
    # Check if we have enough closed trades for analysis
    import sqlite3
    conn = sqlite3.connect(learner.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM trades WHERE status = "closed"')
    closed_count = cursor.fetchone()[0]
    conn.close()
    
    if closed_count >= 5:
        print(f"\n✓ Found {closed_count} closed trades - running analysis...")
        learner.analyze_what_works()
    else:
        print(f"\n⚠️  Only {closed_count} closed trades - need at least 5 for meaningful analysis")
    
    # Step 6: Find new opportunities
    print("\n" + "="*80)
    print("STEP 6: SCANNING FOR NEW OPPORTUNITIES")
    print("="*80)
    
    # Use learned parameters if available, otherwise defaults
    recommendations = run_full_scan_and_recommend(
        account_size=46000,
        max_risk=0.05,
        min_iv_rank=30,  # Will be adjusted by learning system
        max_symbols=20
    )
    
    # Summary
    print("\n" + "="*80)
    print("DAILY ROUTINE COMPLETE")
    print("="*80)
    print(f"✓ Earnings calendar updated")
    print(f"✓ Position earnings warnings checked")
    print(f"✓ Losing positions identified (stop loss recommendations)")
    print(f"✓ Trade changes detected and logged")
    print(f"✓ Performance analysis {'completed' if closed_count >= 5 else 'pending (need more trades)'}")
    print(f"✓ {len(recommendations) if recommendations else 0} new opportunities found")
    print("\nNext steps:")
    print("  1. EXIT any positions flagged as CRITICAL immediately")
    print("  2. Review earnings warnings for open positions")
    print("  3. Review new trade recommendations")
    print("  4. Enter trades in tastytrade if you like them")
    print("  5. Run this script again tomorrow!")
    print("="*80)


if __name__ == "__main__":
    # Create daily_reports directory if it doesn't exist
    reports_dir = Path("daily_reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = reports_dir / f"daily_routine_{timestamp}.md"
    
    # Capture output to both console and file
    output_capture = OutputCapture(report_file)
    sys.stdout = output_capture
    
    try:
        # Add markdown header
        print(f"# Daily Trading Routine Report")
        print(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n---\n")
        
        # Run the routine
        daily_routine()
        
        # Add markdown footer
        print(f"\n---")
        print(f"\n**Report saved to:** `{report_file}`")
        
    finally:
        # Restore stdout and close file
        sys.stdout = output_capture.terminal
        output_capture.close()
        
        print(f"\n✅ Daily routine complete!")
        print(f"📄 Report saved to: {report_file}")

