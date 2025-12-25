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


def daily_routine():
    """Complete daily trading routine."""
    
    print("="*80)
    print("TASTYTRADE DAILY ROUTINE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Step 1: Detect trade changes
    print("\n" + "="*80)
    print("STEP 1: AUTO-DETECTING TRADE CHANGES")
    print("="*80)
    
    detector = AutoTradeDetector()
    accounts = detector.client.get_account_numbers()
    
    for account in accounts:
        detector.detect_changes(account)
    
    # Step 2: Check if we should run learning analysis
    print("\n" + "="*80)
    print("STEP 2: PERFORMANCE ANALYSIS")
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
    
    # Step 3: Find new opportunities
    print("\n" + "="*80)
    print("STEP 3: SCANNING FOR NEW OPPORTUNITIES")
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
    print(f"✓ Trade changes detected and logged")
    print(f"✓ Performance analysis {'completed' if closed_count >= 5 else 'pending (need more trades)'}")
    print(f"✓ {len(recommendations) if recommendations else 0} new opportunities found")
    print("\nNext steps:")
    print("  1. Review new trade recommendations")
    print("  2. Enter trades in tastytrade if you like them")
    print("  3. Run this script again tomorrow!")
    print("="*80)


if __name__ == "__main__":
    daily_routine()
