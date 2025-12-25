"""
Trade Journal System
Tracks recommendations, executions, and outcomes for learning.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class TradeJournal:
    """Database for tracking trade recommendations and outcomes."""
    
    def __init__(self, db_path="trade_journal.db"):
        """Initialize trade journal database."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_recommended TEXT NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                expiration TEXT NOT NULL,
                dte INTEGER,
                short_strike REAL,
                long_strike REAL,
                spread_width REAL,
                expected_credit REAL,
                expected_max_profit REAL,
                expected_max_loss REAL,
                expected_pop REAL,
                iv_rank REAL,
                recommended_contracts INTEGER,
                account_size REAL,
                reason TEXT,
                scanner_version TEXT,
                status TEXT DEFAULT 'recommended'
            )
        ''')
        
        # Trades table (actual executions)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER,
                date_entered TEXT NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                expiration TEXT NOT NULL,
                short_strike REAL,
                long_strike REAL,
                actual_contracts INTEGER,
                entry_credit REAL,
                entry_iv_rank REAL,
                status TEXT DEFAULT 'open',
                date_closed TEXT,
                exit_debit REAL,
                realized_pnl REAL,
                days_held INTEGER,
                max_profit_pct REAL,
                close_reason TEXT,
                notes TEXT,
                FOREIGN KEY (recommendation_id) REFERENCES recommendations (id)
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_calculated TEXT NOT NULL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,
                avg_winner REAL,
                avg_loser REAL,
                profit_factor REAL,
                total_pnl REAL,
                best_strategy TEXT,
                avg_dte_winners INTEGER,
                avg_dte_losers INTEGER,
                avg_iv_rank_winners REAL,
                avg_iv_rank_losers REAL
            )
        ''')
        
        # Learning insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_created TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                description TEXT NOT NULL,
                data TEXT,
                applied BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✓ Trade journal initialized: {self.db_path}")
    
    def log_recommendation(self, opportunity, sizing, reason="Scanner auto-generated"):
        """Log a trade recommendation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO recommendations (
                date_recommended, symbol, strategy, expiration, dte,
                short_strike, long_strike, spread_width, expected_credit,
                expected_max_profit, expected_max_loss, expected_pop,
                iv_rank, recommended_contracts, account_size, reason,
                scanner_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            opportunity.get('symbol'),
            opportunity.get('strategy'),
            opportunity.get('expiration'),
            opportunity.get('dte'),
            opportunity.get('short_strike'),
            opportunity.get('long_strike'),
            opportunity.get('width'),
            opportunity.get('credit'),
            opportunity.get('max_profit'),
            opportunity.get('max_loss'),
            opportunity.get('pop'),
            opportunity.get('iv_rank'),
            sizing.get('contracts'),
            sizing.get('account_size', 46000),
            reason,
            "v1.0"
        ))
        
        rec_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✓ Logged recommendation #{rec_id}: {opportunity.get('symbol')} {opportunity.get('strategy')}")
        return rec_id
    
    def log_trade_entry(self, rec_id, actual_contracts, entry_credit, iv_rank, notes=""):
        """Log when a recommended trade is actually entered."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recommendation details
        cursor.execute('SELECT * FROM recommendations WHERE id = ?', (rec_id,))
        rec = cursor.fetchone()
        
        if not rec:
            print(f"⚠️  Recommendation #{rec_id} not found")
            return None
        
        cursor.execute('''
            INSERT INTO trades (
                recommendation_id, date_entered, symbol, strategy, expiration,
                short_strike, long_strike, actual_contracts, entry_credit,
                entry_iv_rank, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rec_id,
            datetime.now().isoformat(),
            rec[2],  # symbol
            rec[3],  # strategy
            rec[4],  # expiration
            rec[6],  # short_strike
            rec[7],  # long_strike
            actual_contracts,
            entry_credit,
            iv_rank,
            notes
        ))
        
        # Update recommendation status
        cursor.execute('UPDATE recommendations SET status = ? WHERE id = ?', 
                      ('executed', rec_id))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✓ Logged trade entry #{trade_id} from recommendation #{rec_id}")
        return trade_id
    
    def log_trade_exit(self, trade_id, exit_debit, close_reason, notes=""):
        """Log when a trade is closed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get trade details
        cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        trade = cursor.fetchone()
        
        if not trade:
            print(f"⚠️  Trade #{trade_id} not found")
            return
        
        date_entered = datetime.fromisoformat(trade[2])
        date_closed = datetime.now()
        days_held = (date_closed - date_entered).days
        
        entry_credit = trade[9]
        actual_contracts = trade[8]
        
        # Calculate P&L
        realized_pnl = (entry_credit - exit_debit) * 100 * actual_contracts
        
        # Calculate % of max profit achieved
        max_profit_pct = ((entry_credit - exit_debit) / entry_credit * 100) if entry_credit > 0 else 0
        
        cursor.execute('''
            UPDATE trades SET
                date_closed = ?,
                exit_debit = ?,
                realized_pnl = ?,
                days_held = ?,
                max_profit_pct = ?,
                close_reason = ?,
                notes = ?,
                status = 'closed'
            WHERE id = ?
        ''', (
            date_closed.isoformat(),
            exit_debit,
            realized_pnl,
            days_held,
            max_profit_pct,
            close_reason,
            notes,
            trade_id
        ))
        
        conn.commit()
        conn.close()
        
        result = "WIN" if realized_pnl > 0 else "LOSS"
        print(f"✓ Logged trade exit #{trade_id}: {result} ${realized_pnl:,.2f} ({days_held} days)")
        
        # Trigger analysis
        self._analyze_trade(trade_id)
    
    def _analyze_trade(self, trade_id):
        """Analyze why a trade succeeded or failed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get full trade details with recommendation
        cursor.execute('''
            SELECT t.*, r.expected_credit, r.expected_pop, r.iv_rank, r.dte
            FROM trades t
            JOIN recommendations r ON t.recommendation_id = r.id
            WHERE t.id = ?
        ''', (trade_id,))
        
        trade = cursor.fetchone()
        
        if not trade:
            return
        
        realized_pnl = trade[14]
        max_profit_pct = trade[15]
        days_held = trade[14]
        expected_credit = trade[19]
        expected_pop = trade[20]
        iv_rank = trade[21]
        dte = trade[22]
        
        # Determine insights
        insights = []
        
        if realized_pnl > 0:
            # Winner insights
            if max_profit_pct >= 50:
                insights.append({
                    'type': 'winner',
                    'description': f'Followed 50% rule: closed at {max_profit_pct:.1f}% of max profit',
                    'data': json.dumps({'trade_id': trade_id, 'close_pct': max_profit_pct})
                })
            
            if iv_rank > 60:
                insights.append({
                    'type': 'winner',
                    'description': f'High IV rank ({iv_rank:.1f}%) contributed to success',
                    'data': json.dumps({'trade_id': trade_id, 'iv_rank': iv_rank})
                })
        else:
            # Loser insights
            if iv_rank < 40:
                insights.append({
                    'type': 'loser',
                    'description': f'Low IV rank ({iv_rank:.1f}%) may have caused failure',
                    'data': json.dumps({'trade_id': trade_id, 'iv_rank': iv_rank})
                })
            
            if days_held < 7:
                insights.append({
                    'type': 'loser',
                    'description': f'Held only {days_held} days - may have exited too early',
                    'data': json.dumps({'trade_id': trade_id, 'days_held': days_held})
                })
        
        # Store insights
        for insight in insights:
            cursor.execute('''
                INSERT INTO insights (date_created, insight_type, description, data)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                insight['type'],
                insight['description'],
                insight['data']
            ))
        
        conn.commit()
        conn.close()
    
    def get_performance_summary(self):
        """Calculate overall performance metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all closed trades
        cursor.execute('''
            SELECT realized_pnl, days_held, entry_iv_rank, strategy
            FROM trades
            WHERE status = 'closed'
        ''')
        
        trades = cursor.fetchall()
        
        if not trades:
            print("No closed trades yet.")
            return None
        
        total_trades = len(trades)
        winners = [t for t in trades if t[0] > 0]
        losers = [t for t in trades if t[0] <= 0]
        
        win_rate = len(winners) / total_trades * 100 if total_trades > 0 else 0
        avg_winner = sum(t[0] for t in winners) / len(winners) if winners else 0
        avg_loser = sum(t[0] for t in losers) / len(losers) if losers else 0
        total_pnl = sum(t[0] for t in trades)
        
        profit_factor = abs(sum(t[0] for t in winners) / sum(t[0] for t in losers)) if losers and sum(t[0] for t in losers) != 0 else 0
        
        summary = {
            'total_trades': total_trades,
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': win_rate,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'total_pnl': total_pnl,
            'profit_factor': profit_factor
        }
        
        # Store metrics
        cursor.execute('''
            INSERT INTO performance_metrics (
                date_calculated, total_trades, winning_trades,
                losing_trades, win_rate, avg_winner, avg_loser,
                profit_factor, total_pnl
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            total_trades,
            len(winners),
            len(losers),
            win_rate,
            avg_winner,
            avg_loser,
            profit_factor,
            total_pnl
        ))
        
        conn.commit()
        conn.close()
        
        return summary
    
    def display_performance(self):
        """Display performance summary."""
        summary = self.get_performance_summary()
        
        if not summary:
            return
        
        print("\n" + "="*80)
        print("TRADE PERFORMANCE SUMMARY")
        print("="*80)
        print(f"Total Trades:    {summary['total_trades']}")
        print(f"Winners:         {summary['winners']} ({summary['win_rate']:.1f}%)")
        print(f"Losers:          {summary['losers']}")
        print(f"Avg Winner:      ${summary['avg_winner']:.2f}")
        print(f"Avg Loser:       ${summary['avg_loser']:.2f}")
        print(f"Total P&L:       ${summary['total_pnl']:.2f}")
        print(f"Profit Factor:   {summary['profit_factor']:.2f}")
        print("="*80)


if __name__ == "__main__":
    # Initialize journal
    journal = TradeJournal()
    
    # Example: Log a recommendation
    sample_opp = {
        'symbol': 'SPY',
        'strategy': 'Put Credit Spread',
        'expiration': '2026-02-20',
        'dte': 57,
        'short_strike': 565,
        'long_strike': 560,
        'width': 5,
        'credit': 1.85,
        'max_profit': 185,
        'max_loss': 315,
        'pop': 72,
        'iv_rank': 68.5
    }
    
    sample_sizing = {
        'contracts': 7,
        'account_size': 46000
    }
    
    # Log recommendation
    rec_id = journal.log_recommendation(sample_opp, sample_sizing)
    
    # Simulate trade entry
    trade_id = journal.log_trade_entry(rec_id, 7, 1.90, 68.5, "Entered at better price than expected")
    
    # Simulate trade exit (winner - closed at 50% profit)
    # journal.log_trade_exit(trade_id, 0.95, "50% profit rule", "Great trade!")
    
    print("\nTrade journal system ready!")
