"""
Portfolio Analysis Tool - Save to file version
Analyzes current positions, balances, and saves results.
"""

from tastytrade_client import TastytradeClient
from datetime import datetime
import sys


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def analyze_portfolio(output_file=None):
    """Analyze current portfolio positions and balances."""
    
    # Redirect output to file if specified
    if output_file:
        original_stdout = sys.stdout
        sys.stdout = open(output_file, 'w', encoding='utf-8')
    
    try:
        print("="*80)
        print("PORTFOLIO ANALYSIS")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        client = TastytradeClient()
        
        # Get all accounts
        account_numbers = client.get_account_numbers()
        
        if not account_numbers:
            print("\nNo accounts found.")
            return
        
        total_nlv = 0
        all_positions = []
        
        for account_number in account_numbers:
            print(f"\n{'='*80}")
            print(f"ACCOUNT: {account_number}")
            print('='*80)
            
            # Get balances
            balances = client.get_balances(account_number)
            balance_data = balances.get('data', {})
            
            nlv = safe_float(balance_data.get('net-liquidating-value'))
            cash = safe_float(balance_data.get('cash-balance'))
            equity_bp = safe_float(balance_data.get('equity-buying-power'))
            derivative_bp = safe_float(balance_data.get('derivative-buying-power'))
            maintenance = safe_float(balance_data.get('maintenance-requirement'))
            
            total_nlv += nlv
            
            print(f"\n📊 ACCOUNT OVERVIEW")
            print(f"  Net Liquidating Value: ${nlv:,.2f}")
            print(f"  Cash Balance:          ${cash:,.2f}")
            print(f"  Equity Buying Power:   ${equity_bp:,.2f}")
            print(f"  Options Buying Power:  ${derivative_bp:,.2f}")
            print(f"  Maintenance Req:       ${maintenance:,.2f}")
            
            # Calculate utilization
            if nlv > 0:
                cash_pct = (cash / nlv) * 100
                utilization = ((nlv - cash) / nlv) * 100
                print(f"\n  Cash %:                {cash_pct:.1f}%")
                print(f"  Capital Deployed:      {utilization:.1f}%")
            
            # Get positions
            positions = client.get_positions(account_number)
            
            print(f"\n📈 POSITIONS ({len(positions)} total)")
            print("-"*80)
            
            if not positions:
                print("  No positions found.")
                continue
            
            # Group positions by type
            equity_positions = []
            option_positions = []
            other_positions = []
            
            for pos in positions:
                instrument_type = pos.get('instrument-type', '').lower()
                if instrument_type == 'equity':
                    equity_positions.append(pos)
                elif 'option' in instrument_type:
                    option_positions.append(pos)
                else:
                    other_positions.append(pos)
            
            # Analyze equity positions
            if equity_positions:
                print(f"\n  EQUITIES ({len(equity_positions)})")
                print("  " + "-"*76)
                
                total_equity_value = 0
                
                for pos in equity_positions:
                    symbol = pos.get('symbol', 'N/A')
                    quantity = safe_float(pos.get('quantity'))
                    avg_price = safe_float(pos.get('average-open-price'))
                    close_price = safe_float(pos.get('close-price'))
                    
                    # Calculate position value and P&L
                    position_value = quantity * close_price
                    cost_basis = quantity * avg_price
                    pnl = position_value - cost_basis
                    pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                    
                    total_equity_value += position_value
                    
                    pnl_sign = "+" if pnl >= 0 else ""
                    print(f"  {symbol:8} | Qty: {quantity:>8.0f} | Avg: ${avg_price:>8.2f} | "
                          f"Current: ${close_price:>8.2f}")
                    print(f"           | Value: ${position_value:>10,.2f} | "
                          f"P&L: {pnl_sign}${pnl:>8,.2f} ({pnl_sign}{pnl_pct:>6.2f}%)")
                    print()
                
                print(f"  Total Equity Value: ${total_equity_value:,.2f}")
                if nlv > 0:
                    equity_allocation = (total_equity_value / nlv) * 100
                    print(f"  Equity Allocation:  {equity_allocation:.1f}% of portfolio")
            
            # Analyze option positions
            if option_positions:
                print(f"\n  OPTIONS ({len(option_positions)})")
                print("  " + "-"*76)
                
                total_option_value = 0
                
                for pos in option_positions:
                    symbol = pos.get('symbol', 'N/A')
                    quantity = safe_float(pos.get('quantity'))
                    multiplier = safe_float(pos.get('multiplier', 100))
                    avg_price = safe_float(pos.get('average-open-price'))
                    close_price = safe_float(pos.get('close-price'))
                    
                    # Calculate position value and P&L
                    position_value = quantity * close_price * multiplier
                    cost_basis = quantity * avg_price * multiplier
                    pnl = position_value - cost_basis
                    pnl_pct = (pnl / abs(cost_basis) * 100) if cost_basis != 0 else 0
                    
                    total_option_value += position_value
                    
                    # Determine if long or short
                    position_type = "LONG" if quantity > 0 else "SHORT"
                    
                    pnl_sign = "+" if pnl >= 0 else ""
                    print(f"  {symbol:20} | {position_type:5} {abs(quantity):>4.0f} | "
                          f"Avg: ${avg_price:>6.2f}")
                    print(f"                       | Value: ${position_value:>10,.2f} | "
                          f"P&L: {pnl_sign}${pnl:>8,.2f} ({pnl_sign}{pnl_pct:>6.2f}%)")
                    print()
                
                print(f"  Total Options Value: ${total_option_value:,.2f}")
            
            # Other positions
            if other_positions:
                print(f"\n  OTHER ({len(other_positions)})")
                print("  " + "-"*76)
                for pos in other_positions:
                    symbol = pos.get('symbol', 'N/A')
                    instrument_type = pos.get('instrument-type', 'Unknown')
                    quantity = safe_float(pos.get('quantity'))
                    print(f"  {symbol:15} | Type: {instrument_type:15} | Qty: {quantity}")
            
            # Get live orders
            live_orders = client.get_live_orders(account_number)
            
            if live_orders:
                print(f"\n📋 LIVE ORDERS ({len(live_orders)})")
                print("-"*80)
                for order in live_orders:
                    order_type = order.get('order-type', 'N/A')
                    status = order.get('status', 'N/A')
                    legs = order.get('legs', [])
                    
                    print(f"  Order Type: {order_type} | Status: {status}")
                    for leg in legs:
                        action = leg.get('action', 'N/A')
                        qty = leg.get('quantity', 0)
                        symbol = leg.get('symbol', 'N/A')
                        print(f"    - {action} {qty} {symbol}")
                    print()
        
        # Portfolio summary
        print(f"\n{'='*80}")
        print(f"PORTFOLIO SUMMARY")
        print('='*80)
        print(f"Total Net Liquidating Value: ${total_nlv:,.2f}")
        print(f"Number of Accounts: {len(account_numbers)}")
        
        print("\n" + "="*80)
        
    finally:
        if output_file:
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"Portfolio analysis saved to: {output_file}")


if __name__ == "__main__":
    output_file = "portfolio_analysis.txt"
    analyze_portfolio(output_file)
