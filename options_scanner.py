"""
High-Probability Options Scanner
Finds premium selling opportunities using tastytrade methodology.
"""

from tastytrade_client import TastytradeClient
from watchlist import get_full_watchlist
from datetime import datetime, timedelta
import time


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


class OptionsScanner:
    """Scanner for high-probability options trades."""
    
    def __init__(self, min_iv_rank=50, target_dte=45, max_dte=60, 
                 avoid_earnings=True, earnings_window_days=7):
        """
        Initialize scanner.
        
        Args:
            min_iv_rank: Minimum IV rank for screening (default 50%)
            target_dte: Target days to expiration (default 45)
            max_dte: Maximum days to expiration (default 60)
            avoid_earnings: If True, filter out symbols with upcoming earnings
            earnings_window_days: Days ahead to check for earnings (default 7)
        """
        self.client = TastytradeClient()
        self.min_iv_rank = min_iv_rank
        self.target_dte = target_dte
        self.max_dte = max_dte
        self.avoid_earnings = avoid_earnings
        self.earnings_window_days = earnings_window_days
        self.opportunities = []
        
        # Initialize earnings calendar
        try:
            from earnings_calendar import EarningsCalendar
            self.earnings_calendar = EarningsCalendar()
        except:
            self.earnings_calendar = None
            if avoid_earnings:
                print("⚠️  Earnings calendar not available - can't filter earnings")
    
    def scan_for_opportunities(self, symbols=None, max_symbols=20):
        """
        Scan watchlist for high-probability opportunities.
        
        Args:
            symbols: List of symbols to scan (default: top from watchlist)
            max_symbols: Maximum number of symbols to scan
        """
        if symbols is None:
            symbols = get_full_watchlist()[:max_symbols]  # Limit for speed
        
        print(f"\n{'='*80}")
        print(f"OPTIONS SCANNER - High Probability Setups")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        print(f"\nScanning {len(symbols)} symbols...")
        print(f"Criteria: IV Rank > {self.min_iv_rank}%, DTE: ~{self.target_dte} days")
        print("-"*80)
        
        # Get market metrics for all symbols
        print("\n📊 Fetching market metrics...")
        try:
            metrics = self.client.get_market_metrics(symbols)
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return []
        
        # Filter for high IV rank
        high_iv_candidates = []
        
        for metric in metrics:
            symbol = metric.get('symbol', 'N/A')
            iv_rank = safe_float(metric.get('implied-volatility-index-rank'))
            iv_percentile = safe_float(metric.get('implied-volatility-percentile'))
            liquidity = metric.get('liquidity-rating', 0)
            
            if iv_rank >= self.min_iv_rank:
                high_iv_candidates.append({
                    'symbol': symbol,
                    'iv_rank': iv_rank,
                    'iv_percentile': iv_percentile,
                    'liquidity': liquidity,
                    'metric_data': metric
                })
        
        print(f"\n✓ Found {len(high_iv_candidates)} symbols with IV Rank > {self.min_iv_rank}%")
        
        # Filter out earnings if enabled
        if self.avoid_earnings and self.earnings_calendar:
            print(f"\n📅 Checking for earnings in next {self.earnings_window_days} days...")
            
            filtered_candidates = []
            earnings_filtered = []
            
            for candidate in high_iv_candidates:
                symbol = candidate['symbol']
                earnings_info = self.earnings_calendar.check_symbol_earnings(
                    symbol, days_ahead=self.earnings_window_days
                )
                
                if earnings_info:
                    earnings_filtered.append({
                        'symbol': symbol,
                        'earnings_date': earnings_info['earnings_date'],
                        'days_until': earnings_info['days_until']
                    })
                else:
                    filtered_candidates.append(candidate)
            
            if earnings_filtered:
                print(f"\n  ⚠️  Filtered out {len(earnings_filtered)} symbols with upcoming earnings:")
                for item in earnings_filtered[:5]:  # Show first 5
                    print(f"    {item['symbol']:6} - Earnings in {item['days_until']} days ({item['earnings_date']})")
                if len(earnings_filtered) > 5:
                    print(f"    ... and {len(earnings_filtered) - 5} more")
            
            high_iv_candidates = filtered_candidates
            print(f"\n✓ {len(high_iv_candidates)} symbols after earnings filter")
        
        if not high_iv_candidates:
            print("\n⚠️  No opportunities found. Try lowering min_iv_rank or disabling earnings filter.")
            return []
        
        # Sort by IV rank (highest first)
        high_iv_candidates.sort(key=lambda x: x['iv_rank'], reverse=True)
        
        print("\nTop Candidates by IV Rank:")
        for candidate in high_iv_candidates[:10]:
            print(f"  {candidate['symbol']:6} - IV Rank: {candidate['iv_rank']:.1f}% "
                  f"| IV Percentile: {candidate['iv_percentile']:.1f}% "
                  f"| Liquidity: {candidate['liquidity']}")
        
        # Analyze option chains for top candidates
        print(f"\n{'='*80}")
        print("ANALYZING OPTION CHAINS")
        print("-"*80)
        
        opportunities = []
        
        for candidate in high_iv_candidates[:10]:  # Analyze top 10
            symbol = candidate['symbol']
            print(f"\n📈 Analyzing {symbol}...")
            
            try:
                # Get option chain
                chain = self.client.get_option_chain(symbol)
                
                # Find opportunities
                symbol_opps = self._analyze_chain(symbol, chain, candidate)
                opportunities.extend(symbol_opps)
                
                # Rate limit
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ⚠️  Error analyzing {symbol}: {e}")
                continue
        
        # Sort by probability of profit
        opportunities.sort(key=lambda x: x['pop'], reverse=True)
        
        self.opportunities = opportunities
        return opportunities
    
    def _analyze_chain(self, symbol, chain_data, candidate_info):
        """Analyze option chain to find specific trade opportunities."""
        opportunities = []
        
        data = chain_data.get('data', {})
        expirations = data.get('expirations', [])
        
        if not expirations:
            print(f"  No expirations found for {symbol}")
            return opportunities
        
        # Find expiration closest to target DTE
        target_exp = None
        min_dte_diff = float('inf')
        
        for exp in expirations:
            exp_date_str = exp.get('expiration-date')
            if not exp_date_str:
                continue
            
            try:
                exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                dte = (exp_date - datetime.now()).days
                
                # Look for expirations within our target range
                if 30 <= dte <= self.max_dte:
                    dte_diff = abs(dte - self.target_dte)
                    if dte_diff < min_dte_diff:
                        min_dte_diff = dte_diff
                        target_exp = exp
            except:
                continue
        
        if not target_exp:
            print(f"  No suitable expiration found (looking for ~{self.target_dte} DTE)")
            return opportunities
        
        exp_date_str = target_exp.get('expiration-date')
        dte = (datetime.strptime(exp_date_str, '%Y-%m-%d') - datetime.now()).days
        
        print(f"  ✓ Found expiration: {exp_date_str} ({dte} DTE)")
        
        # Look for put credit spread opportunities
        put_spread = self._find_put_credit_spread(symbol, target_exp, candidate_info, dte)
        if put_spread:
            opportunities.append(put_spread)
        
        # Look for call credit spread if IV rank is very high
        if candidate_info['iv_rank'] > 70:
            call_spread = self._find_call_credit_spread(symbol, target_exp, candidate_info, dte)
            if call_spread:
                opportunities.append(call_spread)
        
        return opportunities
    
    def _find_put_credit_spread(self, symbol, expiration, candidate_info, dte):
        """Find optimal put credit spread setup."""
        strikes = expiration.get('strikes', [])
        
        if not strikes:
            return None
        
        # Find ATM strike
        atm_price = safe_float(expiration.get('underlying-price', 0))
        
        # Look for short strike around 0.30 delta (30% probability ITM)
        # For puts, this is below current price
        target_short_strike = atm_price * 0.95  # Rough approximation
        
        # Find strikes
        put_strikes = []
        for strike_data in strikes:
            strike_price = safe_float(strike_data.get('strike-price'))
            
            # Get put option data
            put_option = strike_data.get('put')
            if not put_option:
                continue
            
            delta = safe_float(put_option.get('delta', 0))
            bid = safe_float(put_option.get('bid', 0))
            ask = safe_float(put_option.get('ask', 0))
            
            # We want puts with delta around -0.30 (short puts)
            if -0.35 <= delta <= -0.25 and bid > 0 and ask > 0:
                put_strikes.append({
                    'strike': strike_price,
                    'delta': delta,
                    'bid': bid,
                    'ask': ask,
                    'mid': (bid + ask) / 2
                })
        
        if not put_strikes:
            return None
        
        # Sort by strike (descending for puts)
        put_strikes.sort(key=lambda x: x['strike'], reverse=True)
        
        # Short strike = highest strike with ~0.30 delta
        short_strike_data = put_strikes[0]
        short_strike = short_strike_data['strike']
        
        # Long strike = $5 or $10 below short strike
        width = 5 if short_strike < 100 else 10
        long_strike = short_strike - width
        
        # Find long strike data
        long_strike_data = None
        for strike_data in strikes:
            if abs(safe_float(strike_data.get('strike-price')) - long_strike) < 0.01:
                put_option = strike_data.get('put')
                if put_option:
                    long_strike_data = {
                        'strike': long_strike,
                        'bid': safe_float(put_option.get('bid', 0)),
                        'ask': safe_float(put_option.get('ask', 0)),
                        'mid': (safe_float(put_option.get('bid', 0)) + 
                               safe_float(put_option.get('ask', 0))) / 2
                    }
                break
        
        if not long_strike_data:
            return None
        
        # Calculate spread credit
        credit = short_strike_data['mid'] - long_strike_data['mid']
        max_profit = credit * 100  # Per spread
        max_loss = (width - credit) * 100
        pop = abs(short_strike_data['delta']) * 100  # Rough approximation
        
        # We want credit to be at least 1/3 of width
        if credit < (width / 3):
            return None
        
        return {
            'symbol': symbol,
            'strategy': 'Put Credit Spread',
            'iv_rank': candidate_info['iv_rank'],
            'expiration': expiration.get('expiration-date'),
            'dte': dte,
            'short_strike': short_strike,
            'long_strike': long_strike,
            'width': width,
            'credit': credit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'pop': pop,
            'return_on_risk': (credit / width) * 100
        }
    
    def _find_call_credit_spread(self, symbol, expiration, candidate_info, dte):
        """Find optimal call credit spread setup (for very high IV)."""
        # Similar logic to put spread but for calls
        # Implementation similar to above but targeting calls
        return None  # Placeholder for now
    
    def display_opportunities(self, top_n=10):
        """Display top trading opportunities."""
        if not self.opportunities:
            print("\nNo opportunities found.")
            return
        
        print(f"\n{'='*80}")
        print(f"TOP {min(top_n, len(self.opportunities))} TRADING OPPORTUNITIES")
        print(f"{'='*80}\n")
        
        for i, opp in enumerate(self.opportunities[:top_n], 1):
            print(f"{i}. {opp['symbol']} - {opp['strategy']}")
            print(f"   IV Rank: {opp['iv_rank']:.1f}% | Expiration: {opp['expiration']} ({opp['dte']} DTE)")
            print(f"   Sell ${opp['short_strike']:.2f} Put / Buy ${opp['long_strike']:.2f} Put")
            print(f"   Credit: ${opp['credit']:.2f} | Width: ${opp['width']:.0f}")
            print(f"   Max Profit: ${opp['max_profit']:.0f} | Max Loss: ${opp['max_loss']:.0f}")
            print(f"   Return on Risk: {opp['return_on_risk']:.1f}% | Probability: {opp['pop']:.0f}%")
            print()


if __name__ == "__main__":
    scanner = OptionsScanner(min_iv_rank=40)  # Lower threshold for testing
    
    # Scan with default watchlist
    opportunities = scanner.scan_for_opportunities(max_symbols=15)
    
    # Display results
    scanner.display_opportunities(top_n=10)
