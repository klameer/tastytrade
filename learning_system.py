"""
Learning System - Analyzes past trades to improve future recommendations.
"""

import sqlite3
from trade_journal import TradeJournal
import json


class TradeLearningSystem:
    """Analyze historical performance to improve scanner parameters."""
    
    def __init__(self, journal_path="trade_journal.db"):
        self.journal = TradeJournal(journal_path)
        self.db_path = journal_path
    
    def analyze_what_works(self):
        """Analyze which conditions lead to winning trades."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("LEARNING ANALYSIS: What Works?")
        print("="*80)
        
        # Analyze IV rank for winners vs losers
        cursor.execute('''
            SELECT 
                AVG(CASE WHEN realized_pnl > 0 THEN entry_iv_rank END) as avg_iv_winners,
                AVG(CASE WHEN realized_pnl <= 0 THEN entry_iv_rank END) as avg_iv_losers
            FROM trades
            WHERE status = 'closed'
        ''')
        
        iv_analysis = cursor.fetchone()
        
        if iv_analysis[0]:
            print(f"\nIV RANK ANALYSIS:")
            print(f"  Winners avg IV:  {iv_analysis[0]:.1f}%")
            print(f"  Losers avg IV:   {iv_analysis[1]:.1f}%")
            
            if iv_analysis[0] > iv_analysis[1] + 10:
                print(f"  💡 INSIGHT: Higher IV rank ({iv_analysis[0]:.1f}%) correlates with wins")
                print(f"  → RECOMMENDATION: Increase min_iv_rank threshold to {iv_analysis[0] - 5:.0f}%")
        
        # Analyze DTE for winners vs losers  
        cursor.execute('''
            SELECT t.days_held, r.dte
            FROM trades t
            JOIN recommendations r ON t.recommendation_id = r.id
            WHERE t.status = 'closed' AND t.realized_pnl > 0
        ''')
        
        winner_days = cursor.fetchall()
        
        cursor.execute('''
            SELECT t.days_held, r.dte
            FROM trades t
            JOIN recommendations r ON t.recommendation_id = r.id
            WHERE t.status = 'closed' AND t.realized_pnl <= 0
        ''')
        
        loser_days = cursor.fetchall()
        
        if winner_days:
            avg_winner_dte = sum(d[1] for d in winner_days) / len(winner_days)
            print(f"\nDTE ANALYSIS:")
            print(f"  Winners avg DTE: {avg_winner_dte:.0f} days")
            
            if loser_days:
                avg_loser_dte = sum(d[1] for d in loser_days) / len(loser_days)
                print(f"  Losers avg DTE:  {avg_loser_dte:.0f} days")
        
        # Analyze by symbol
        cursor.execute('''
            SELECT symbol, 
                   COUNT(*) as total,
                   SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                   AVG(realized_pnl) as avg_pnl
            FROM trades
            WHERE status = 'closed'
            GROUP BY symbol
            HAVING COUNT(*) >= 2
            ORDER BY avg_pnl DESC
        ''')
        
        symbol_performance = cursor.fetchall()
        
        if symbol_performance:
            print(f"\nSYMBOL PERFORMANCE (2+ trades):")
            for symbol, total, wins, avg_pnl in symbol_performance:
                win_rate = (wins / total * 100) if total > 0 else 0
                print(f"  {symbol:6} - {total} trades, {win_rate:.0f}% win rate, Avg P&L: ${avg_pnl:.2f}")
        
        # Analyze close reasons
        cursor.execute('''
            SELECT close_reason, COUNT(*), AVG(realized_pnl)
            FROM trades
            WHERE status = 'closed'
            GROUP BY close_reason
        ''')
        
        close_reasons = cursor.fetchall()
        
        if close_reasons:
            print(f"\nCLOSE REASONS:")
            for reason, count, avg_pnl in close_reasons:
                print(f"  {reason}: {count} trades, Avg P&L: ${avg_pnl:.2f}")
        
        conn.close()
        
        return self._generate_recommendations()
    
    def _generate_recommendations(self):
        """Generate scanner parameter recommendations based on analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        recommendations = []
        
        # Get overall win rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins
            FROM trades
            WHERE status = 'closed'
        ''')
        
        result = cursor.fetchone()
        
        if result[0] >= 10:  # Need at least 10 trades
            win_rate = (result[1] / result[0] * 100) if result[0] > 0 else 0
            
            print(f"\n{'='*80}")
            print("PARAMETER RECOMMENDATIONS")
            print("="*80)
            
            if win_rate < 50:
                recommendations.append({
                    'parameter': 'min_iv_rank',
                    'action': 'increase',
                    'reason': f'Win rate ({win_rate:.1f}%) below target (50%+)',
                    'suggested_value': 60
                })
                print("\n⚠️  Win rate below 50% - Consider:")
                print("  - Increase min_iv_rank to 60% (only trade very elevated IV)")
                print("  - Focus on symbols with proven track record")
                print("  - Tighten strike selection (closer to 0.30 delta)")
            
            elif win_rate > 70:
                recommendations.append({
                    'parameter': 'min_iv_rank',
                    'action': 'decrease',
                    'reason': f'Win rate ({win_rate:.1f}%) very high - can be more aggressive',
                    'suggested_value': 40
                })
                print("\n✓ Excellent win rate - Consider:")
                print("  - Lower min_iv_rank to 40% (find more opportunities)")
                print("  - Increase position sizes slightly")
                print("  - Explore lower delta strikes for higher credit")
        
        conn.close()
        
        return recommendations
    
    def generate_weekly_report(self):
        """Generate weekly performance and learning report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get this week's trades
        cursor.execute('''
            SELECT COUNT(*), SUM(realized_pnl)
            FROM trades
            WHERE status = 'closed'
            AND DATE(date_closed) >= DATE('now', '-7 days')
        ''')
        
        week_stats = cursor.fetchone()
        
        # Get insights from this week
        cursor.execute('''
            SELECT insight_type, description, date_created
            FROM insights
            WHERE DATE(date_created) >= DATE('now', '-7 days')
            ORDER BY date_created DESC
        ''')
        
        insights = cursor.fetchall()
        
        conn.close()
        
        print("\n" + "="*80)
        print("WEEKLY PERFORMANCE REPORT")
        print("="*80)
        
        if week_stats[0]:
            print(f"\nThis Week:")
            print(f"  Closed Trades:  {week_stats[0]}")
            print(f"  Total P&L:      ${week_stats[1]:.2f}")
        
        if insights:
            print(f"\nKey Insights:")
            for insight_type, description, date_created in insights:
                print(f"  [{insight_type.upper()}] {description}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    learner = TradeLearningSystem()
    
    # Run analysis
    learner.analyze_what_works()
    
    # Generate weekly report
    learner.generate_weekly_report()
