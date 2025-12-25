"""
Automatic Trade Detector
Compares current positions with last snapshot to auto-detect entries and exits.
No manual logging needed!
"""

import sqlite3
from tastytrade_client import TastytradeClient
from trade_journal import TradeJournal
from datetime import datetime
import json
import hashlib


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


class AutoTradeDetector:
    """Automatically detect trades by comparing position snapshots."""
    
    def __init__(self, journal_db="trade_journal.db"):
        self.client = TastytradeClient()
        self.journal = TradeJournal(journal_db)
        self.db_path = journal_db
        self._init_snapshot_table()
    
    def _init_snapshot_table(self):
        """Create position snapshot table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS position_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                account_number TEXT NOT NULL,
                position_hash TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                instrument_type TEXT NOT NULL,
                avg_open_price REAL,
                close_price REAL,
                position_value REAL,
                raw_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_position_hash 
            ON position_snapshots(position_hash)
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_position_hash(self, position):
        """Create unique hash for a position."""
        # Use symbol + instrument type to identify position
        symbol = position.get('symbol', '')
        inst_type = position.get('instrument-type', '')
        
        # For options, include underlying + expiration + strike from symbol
        # This creates a unique identifier for each position
        hash_string = f"{symbol}_{inst_type}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def take_snapshot(self, account_number):
        """Take snapshot of current positions."""
        print(f"\n📸 Taking position snapshot for account {account_number}...")
        
        positions = self.client.get_positions(account_number)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        snapshot_date = datetime.now().isoformat()
        
        for pos in positions:
            position_hash = self._create_position_hash(pos)
            
            cursor.execute('''
                INSERT INTO position_snapshots (
                    snapshot_date, account_number, position_hash,
                    symbol, quantity, instrument_type,
                    avg_open_price, close_price, position_value, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_date,
                account_number,
                position_hash,
                pos.get('symbol', ''),
                safe_float(pos.get('quantity')),
                pos.get('instrument-type', ''),
                safe_float(pos.get('average-open-price')),
                safe_float(pos.get('close-price')),
                safe_float(pos.get('quantity')) * safe_float(pos.get('close-price')),
                json.dumps(pos)
            ))
        
        conn.commit()
        conn.close()
        
        print(f"  ✓ Snapshot saved: {len(positions)} positions")
    
    def detect_changes(self, account_number):
        """
        Compare current positions with last snapshot.
        Auto-detect new entries and exits.
        """
        print(f"\n{'='*80}")
        print(f"AUTO-DETECTING TRADES - Account {account_number}")
        print(f"{'='*80}\n")
        
        # Get current positions
        current_positions = self.client.get_positions(account_number)
        
        # Get last snapshot
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the last snapshot date
        cursor.execute('''
            SELECT DISTINCT snapshot_date
            FROM position_snapshots
            WHERE account_number = ?
            ORDER BY snapshot_date DESC
            LIMIT 2
        ''', (account_number,))
        
        snapshot_dates = cursor.fetchall()
        
        if len(snapshot_dates) < 2:
            print("⚠️  Need at least 2 snapshots to detect changes.")
            print("   Taking first snapshot now...")
            self.take_snapshot(account_number)
            conn.close()
            return
        
        last_snapshot_date = snapshot_dates[1][0]  # Second most recent (prev)
        
        # Get positions from last snapshot
        cursor.execute('''
            SELECT position_hash, symbol, quantity, instrument_type, raw_data
            FROM position_snapshots
            WHERE account_number = ? AND snapshot_date = ?
        ''', (account_number, last_snapshot_date))
        
        last_positions = cursor.fetchall()
        
        # Create lookup dicts
        last_pos_dict = {row[0]: row for row in last_positions}
        
        current_pos_dict = {}
        for pos in current_positions:
            pos_hash = self._create_position_hash(pos)
            current_pos_dict[pos_hash] = pos
        
        # Detect NEW positions (entries)
        new_positions = []
        for pos_hash, pos in current_pos_dict.items():
            if pos_hash not in last_pos_dict:
                new_positions.append(pos)
        
        # Detect CLOSED positions (exits)
        closed_positions = []
        for pos_hash, pos_data in last_pos_dict.items():
            if pos_hash not in current_pos_dict:
                closed_positions.append(pos_data)
        
        # Detect CHANGED positions (quantity changes - could be partial close or add)
        changed_positions = []
        for pos_hash in set(last_pos_dict.keys()) & set(current_pos_dict.keys()):
            last_qty = last_pos_dict[pos_hash][2]
            current_qty = current_pos_dict[pos_hash].get('quantity', 0)
            
            if abs(safe_float(current_qty) - safe_float(last_qty)) > 0.01:
                changed_positions.append({
                    'symbol': current_pos_dict[pos_hash].get('symbol'),
                    'last_qty': last_qty,
                    'current_qty': current_qty,
                    'change': safe_float(current_qty) - safe_float(last_qty)
                })
        
        # Report findings
        print(f"📊 POSITION CHANGES SINCE {last_snapshot_date[:10]}")
        print("-"*80)
        
        if new_positions:
            print(f"\n✅ NEW POSITIONS DETECTED ({len(new_positions)}):")
            for pos in new_positions:
                symbol = pos.get('symbol', 'N/A')
                quantity = safe_float(pos.get('quantity'))
                inst_type = pos.get('instrument-type', '')
                avg_price = safe_float(pos.get('average-open-price'))
                
                print(f"  + {symbol:20} | {inst_type:15} | Qty: {quantity:>8.2f} | Avg Price: ${avg_price:.2f}")
                
                # Try to match with recommendations and auto-log
                self._auto_log_entry(pos, account_number)
        else:
            print("\n  No new positions detected.")
        
        if closed_positions:
            print(f"\n❌ CLOSED POSITIONS DETECTED ({len(closed_positions)}):")
            for pos_data in closed_positions:
                symbol = pos_data[1]
                quantity = pos_data[2]
                inst_type = pos_data[3]
                
                print(f"  - {symbol:20} | {inst_type:15} | Qty: {quantity:>8.2f}")
                
                # Auto-log exit
                self._auto_log_exit(pos_data, current_positions, account_number)
        else:
            print("\n  No closed positions detected.")
        
        if changed_positions:
            print(f"\n🔄 QUANTITY CHANGES DETECTED ({len(changed_positions)}):")
            for change in changed_positions:
                print(f"  ~ {change['symbol']:20} | {change['last_qty']:>8.2f} → {change['current_qty']:>8.2f} "
                      f"({change['change']:+.2f})")
        
        conn.close()
        
        # Take new snapshot for next comparison
        self.take_snapshot(account_number)
        
        print(f"\n{'='*80}\n")
    
    def _auto_log_entry(self, position, account_number):
        """Automatically log position entry to trade journal."""
        symbol = position.get('symbol', '')
        quantity = safe_float(position.get('quantity'))
        avg_price = safe_float(position.get('average-open-price'))
        inst_type = position.get('instrument-type', '')
        
        # Only auto-log options for now
        if 'option' not in inst_type.lower():
            return
        
        # Try to match with recent recommendations
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Look for matching recommendation in last 7 days
        cursor.execute('''
            SELECT id, symbol, strategy, short_strike, long_strike, 
                   expected_credit, recommended_contracts, iv_rank
            FROM recommendations
            WHERE symbol = ?
            AND status = 'recommended'
            AND DATE(date_recommended) >= DATE('now', '-7 days')
            ORDER BY date_recommended DESC
            LIMIT 1
        ''', (symbol.split()[0],))  # Extract underlying from option symbol
        
        rec = cursor.fetchone()
        
        if rec:
            rec_id = rec[0]
            
            # Log the trade entry
            trade_id = self.journal.log_trade_entry(
                rec_id=rec_id,
                actual_contracts=abs(int(quantity)),
                entry_credit=avg_price,
                iv_rank=rec[7],
                notes=f"Auto-detected from position snapshot"
            )
            
            print(f"    → Auto-logged to trade journal (Trade #{trade_id}, Rec #{rec_id})")
        else:
            print(f"    ⚠️  No matching recommendation found - manual review needed")
        
        conn.close()
    
    def _auto_log_exit(self, pos_data, current_positions, account_number):
        """Automatically log position exit to trade journal."""
        symbol = pos_data[1]
        
        # Check if this position had an open trade in journal
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Look for open trade with matching symbol
        cursor.execute('''
            SELECT id, entry_credit, actual_contracts
            FROM trades
            WHERE symbol = ?
            AND status = 'open'
            ORDER BY date_entered DESC
            LIMIT 1
        ''', (symbol.split()[0],))  # Extract underlying
        
        trade = cursor.fetchone()
        
        if trade:
            trade_id = trade[0]
            entry_credit = trade[1]
            
            # Position closed means we exited at $0 debit (or small value)
            # This is approximate - actual exit price would need separate tracking
            exit_debit = 0.05  # Assume small residual value
            
            self.journal.log_trade_exit(
                trade_id=trade_id,
                exit_debit=exit_debit,
                close_reason="Auto-detected position close",
                notes="Position no longer in account - assuming expired or closed near 0"
            )
            
            print(f"    → Auto-logged exit to trade journal (Trade #{trade_id})")
        
        conn.close()


def run_auto_detection():
    """Main function to run automatic trade detection."""
    detector = AutoTradeDetector()
    
    # Get account
    accounts = detector.client.get_account_numbers()
    
    if not accounts:
        print("No accounts found.")
        return
    
    # Detect changes for each account
    for account_number in accounts:
        detector.detect_changes(account_number)


if __name__ == "__main__":
    run_auto_detection()
