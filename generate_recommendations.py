"""
Complete Trading System
Combines scanner, position sizer, and generates trade recommendations.
"""

from options_scanner import OptionsScanner
from position_sizer import PositionSizer
from watchlist import get_full_watchlist
import json
from datetime import datetime


def run_full_scan_and_recommend(account_size=46000, max_risk=0.05, min_iv_rank=30, max_symbols=20):
    """
    Run complete scan and generate trade recommendations.
    
    Args:
        account_size: Total account value
        max_risk: Maximum risk per trade (default 5%)
        min_iv_rank: Minimum IV rank threshold (default 30%)
        max_symbols: Maximum symbols to scan
    """
    print("="*80)
    print("TASTYTRADE HIGH-PROBABILITY OPTIONS SCANNER")
    print("="*80)
    print(f"\nAccount Size: ${account_size:,.2f}")
    print(f"Max Risk Per Trade: {max_risk*100}% (${account_size*max_risk:,.2f})")
    print(f"Min IV Rank: {min_iv_rank}%")
    
    # Initialize scanner and sizer
    scanner = OptionsScanner(min_iv_rank=min_iv_rank)
    sizer = PositionSizer(account_size=account_size, max_risk_per_trade=max_risk)
    
    # Run scan
    opportunities = scanner.scan_for_opportunities(max_symbols=max_symbols)
    
    if not opportunities:
        print("\n⚠️  No opportunities found with current criteria.")
        print("\nTips:")
        print("  - Lower min_iv_rank (currently {})".format(min_iv_rank))
        print("  - Scan during market hours for fresh data")
        print("  - Markets may be in low volatility environment")
        return []
    
    # Generate recommendations with position sizing
    print(f"\n{'='*80}")
    print("TRADE RECOMMENDATIONS WITH POSITION SIZING")
    print(f"{'='*80}\n")
    
    recommendations = []
    
    for i, opp in enumerate(opportunities[:5], 1):  # Top 5
        sizing = sizer.calculate_position_details(opp)
        
        if sizing['meets_criteria']:
            rec = sizer.format_trade_recommendation(opp, sizing)
            print(f"\nRECOMMENDATION #{i}")
            print(rec)
            
            recommendations.append({
                'opportunity': opp,
                'sizing': sizing,
                'recommendation': rec
            })
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"trade_recommendations_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(f"TASTYTRADE OPTIONS SCANNER - RECOMMENDATIONS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Account Size: ${account_size:,.2f}\n")
        f.write(f"Max Risk: {max_risk*100}%\n")
        f.write(f"\n{'='*80}\n\n")
        
        for i, rec in enumerate(recommendations, 1):
            f.write(f"\nRECOMMENDATION #{i}\n")
            f.write(rec['recommendation'])
            f.write("\n\n")
    
    print(f"\n{'='*80}")
    print(f"Recommendations saved to: {filename}")
    print(f"{'='*80}\n")
    
    return recommendations


def create_sample_recommendations():
    """Create sample recommendations for demonstration."""
    print("\n" + "="*80)
    print("SAMPLE TRADE RECOMMENDATIONS (Example Data)")
    print("="*80 + "\n")
    
    # Sample opportunities (for demonstration when markets are closed)
    sample_opps = [
        {
            'symbol': 'SPY',
            'strategy': 'Put Credit Spread',
            'expiration': '2026-02-20',
            'dte': 57,
            'short_strike': 565,
            'long_strike': 560,
            'width': 5,
            'credit': 1.85,
            'iv_rank': 68.5,
            'pop': 72,
            'return_on_risk': 37,
            'max_profit': 185,
            'max_loss': 315
        },
        {
            'symbol': 'QQQ',
            'strategy': 'Put Credit Spread',
            'expiration': '2026-02-13',
            'dte': 50,
            'short_strike': 480,
            'long_strike': 475,
            'width': 5,
            'credit': 1.70,
            'iv_rank': 71.2,
            'pop': 70,
            'return_on_risk': 34,
            'max_profit': 170,
            'max_loss': 330
        },
        {
            'symbol': 'NVDA',
            'strategy': 'Put Credit Spread',
            'expiration': '2026-02-20',
            'dte': 57,
            'short_strike': 130,
            'long_strike': 125,
            'width': 5,
            'credit': 1.75,
            'iv_rank': 65.8,
            'pop': 71,
            'return_on_risk': 35,
            'max_profit': 175,
            'max_loss': 325
        }
    ]
    
    sizer = PositionSizer(account_size=46000, max_risk_per_trade=0.05)
    
    for i, opp in enumerate(sample_opps, 1):
        sizing = sizer.calculate_position_details(opp)
        rec = sizer.format_trade_recommendation(opp, sizing)
        print(f"SAMPLE RECOMMENDATION #{i}")
        print(rec)
        print("\n")


if __name__ == "__main__":
    # Try to run live scan
    print("Attempting live market scan...")
    recommendations = run_full_scan_and_recommend(
        account_size=46000,
        max_risk=0.05,
        min_iv_rank=30,  # Lower threshold
        max_symbols=15
    )
    
    # If no live recommendations, show samples
    if not recommendations:
        print("\n⚠️  No live opportunities found (markets may be closed).")
        print("Showing sample recommendations...\n")
        create_sample_recommendations()
