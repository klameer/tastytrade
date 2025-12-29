"""
Earnings Calendar Integration
Fetches earnings dates and integrates with trading system.
"""

import yfinance as yf
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Optional


class EarningsCalendar:
    """Track and manage earnings dates for watchlist symbols."""
    
    def __init__(self, db_path="trade_journal.db"):
        self.db_path = db_path
        self._init_earnings_table()
    
    def _init_earnings_table(self):
        """Create earnings calendar table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS earnings_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                earnings_date TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                confirmed BOOLEAN DEFAULT 0,
                UNIQUE(symbol, earnings_date)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_earnings_date 
            ON earnings_calendar(earnings_date)
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_earnings_date(self, symbol: str) -> Optional[str]:
        """
        Fetch next earnings date for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Earnings date string (YYYY-MM-DD) or None
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get earnings date from calendar
            calendar = ticker.calendar
            
            if calendar is not None and 'Earnings Date' in calendar:
                earnings_dates = calendar['Earnings Date']
                
                if earnings_dates is not None:
                    # Get the next upcoming earnings date
                    if isinstance(earnings_dates, list) and len(earnings_dates) > 0:
                        next_earnings = earnings_dates[0]
                    else:
                        next_earnings = earnings_dates
                    
                    # Convert to string if datetime
                    if hasattr(next_earnings, 'strftime'):
                        return next_earnings.strftime('%Y-%m-%d')
                    elif isinstance(next_earnings, str):
                        return next_earnings
            
            return None
            
        except Exception as e:
            print(f"  Warning: Could not fetch earnings for {symbol}: {e}")
            return None
    
    def update_earnings(self, symbols: List[str]):
        """
        Update earnings dates for list of symbols.
        
        Args:
            symbols: List of stock symbols
        """
        print(f"\n📅 Updating earnings calendar for {len(symbols)} symbols...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updated = 0
        
        for symbol in symbols:
            earnings_date = self.fetch_earnings_date(symbol)
            
            if earnings_date:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO earnings_calendar 
                        (symbol, earnings_date, last_updated, confirmed)
                        VALUES (?, ?, ?, 1)
                    ''', (symbol, earnings_date, datetime.now().isoformat()))
                    
                    updated += 1
                    
                except Exception as e:
                    print(f"  Error saving earnings for {symbol}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"  ✓ Updated {updated} earnings dates")
    
    def get_earnings_within_days(self, days: int = 7) -> List[Dict]:
        """
        Get symbols with earnings in next N days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of dicts with symbol and earnings_date
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        
        cursor.execute('''
            SELECT symbol, earnings_date
            FROM earnings_calendar
            WHERE DATE(earnings_date) BETWEEN DATE(?) AND DATE(?)
            ORDER BY earnings_date
        ''', (today.isoformat(), end_date.isoformat()))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'symbol': row[0],
                'earnings_date': row[1],
                'days_until': (datetime.strptime(row[1], '%Y-%m-%d').date() - today).days
            })
        
        conn.close()
        
        return results
    
    def check_symbol_earnings(self, symbol: str, days_ahead: int = 7) -> Optional[Dict]:
        """
        Check if symbol has earnings in next N days.
        
        Args:
            symbol: Stock symbol
            days_ahead: Days to look ahead
            
        Returns:
            Dict with earnings info or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        cursor.execute('''
            SELECT earnings_date
            FROM earnings_calendar
            WHERE symbol = ?
            AND DATE(earnings_date) BETWEEN DATE(?) AND DATE(?)
        ''', (symbol, today.isoformat(), end_date.isoformat()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            earnings_date = datetime.strptime(result[0], '%Y-%m-%d').date()
            days_until = (earnings_date - today).days
            
            return {
                'symbol': symbol,
                'earnings_date': result[0],
                'days_until': days_until
            }
        
        return None
    
    def display_upcoming_earnings(self, days: int = 14):
        """Display upcoming earnings in a formatted table."""
        earnings = self.get_earnings_within_days(days)
        
        if not earnings:
            print(f"\n  No earnings in next {days} days")
            return
        
        print(f"\n📅 EARNINGS IN NEXT {days} DAYS")
        print("-" * 60)
        print(f"{'Symbol':<8} {'Date':<12} {'Days Until':<15} {'Action':<20}")
        print("-" * 60)
        
        for item in earnings:
            days_until = item['days_until']
            
            if days_until <= 2:
                action = "⚠️  IMMINENT - Avoid"
            elif days_until <= 5:
                action = "⚡ Soon - Consider exit"
            else:
                action = "📊 Upcoming - Monitor"
            
            print(f"{item['symbol']:<8} {item['earnings_date']:<12} "
                  f"{days_until} days{'':<8} {action:<20}")
        
        print("-" * 60)


def check_positions_for_earnings(calendar: EarningsCalendar, positions: List[Dict]) -> List[Dict]:
    """
    Check if any open positions have upcoming earnings.
    
    Args:
        calendar: EarningsCalendar instance
        positions: List of position dicts
        
    Returns:
        List of positions with upcoming earnings
    """
    warnings = []
    
    for pos in positions:
        symbol_full = pos.get('symbol', '')
        
        # Extract underlying symbol (first part before space for options)
        symbol = symbol_full.split()[0] if ' ' in symbol_full else symbol_full
        
        # Check for earnings in next 14 days
        earnings_info = calendar.check_symbol_earnings(symbol, days_ahead=14)
        
        if earnings_info:
            warnings.append({
                'position': pos,
                'earnings_info': earnings_info
            })
    
    return warnings


if __name__ == "__main__":
    # Test earnings calendar
    from watchlist import get_full_watchlist
    
    calendar = EarningsCalendar()
    
    # Update earnings for watchlist (sample)
    symbols = get_full_watchlist()[:10]  # Test with first 10
    calendar.update_earnings(symbols)
    
    # Show upcoming earnings
    calendar.display_upcoming_earnings(14)
