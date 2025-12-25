"""
Portfolio Exit Plan Calculator
Calculates proceeds from exiting all current positions and available capital.
"""

from tastytrade_client import TastytradeClient
from datetime import datetime


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def calculate_exit_plan():
    """Calculate proceeds from exiting all positions."""
    
    print("="*80)
    print("PORTFOLIO EXIT PLAN")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    client = TastytradeClient()
    account_numbers = client.get_account_numbers()
    
    if not account_numbers:
        print("\nNo accounts found.")
        return
    
    # Focus on the active account
    account_number = account_numbers[0]
    
    print(f"\nAccount: {account_number}")
    print("="*80)
    
    # Get current balances
    balances = client.get_balances(account_number)
    balance_data = balances.get('data', {})
    
    current_nlv = safe_float(balance_data.get('net-liquidating-value'))
    current_cash = safe_float(balance_data.get('cash-balance'))
    
    print(f"\n📊 CURRENT PORTFOLIO")
    print(f"  Net Liquidating Value: ${current_nlv:,.2f}")
    print(f"  Cash Balance:          ${current_cash:,.2f}")
    
    # Get all positions
    positions = client.get_positions(account_number)
    
    print(f"\n📋 POSITIONS TO EXIT ({len(positions)} total)")
    print("-"*80)
    
    total_exit_value = 0
    total_realized_pnl = 0
    
    equity_exits = []
    option_exits = []
    
    for pos in positions:
        symbol = pos.get('symbol', 'N/A')
        instrument_type = pos.get('instrument-type', '').lower()
        quantity = safe_float(pos.get('quantity'))
        multiplier = safe_float(pos.get('multiplier', 100 if 'option' in instrument_type else 1))
        avg_price = safe_float(pos.get('average-open-price'))
        close_price = safe_float(pos.get('close-price'))
        
        # Calculate exit value and realized P&L
        exit_value = quantity * close_price * multiplier
        cost_basis = quantity * avg_price * multiplier
        realized_pnl = exit_value - cost_basis
        pnl_pct = (realized_pnl / abs(cost_basis) * 100) if cost_basis != 0 else 0
        
        total_exit_value += exit_value
        total_realized_pnl += realized_pnl
        
        exit_data = {
            'symbol': symbol,
            'type': instrument_type,
            'quantity': quantity,
            'avg_price': avg_price,
            'exit_price': close_price,
            'exit_value': exit_value,
            'realized_pnl': realized_pnl,
            'pnl_pct': pnl_pct
        }
        
        if instrument_type == 'equity':
            equity_exits.append(exit_data)
        else:
            option_exits.append(exit_data)
    
    # Display equity exits
    if equity_exits:
        print("\n  EQUITY EXITS")
        print("  " + "-"*76)
        for exit in equity_exits:
            pnl_sign = "+" if exit['realized_pnl'] >= 0 else ""
            print(f"  {exit['symbol']:8} | Qty: {exit['quantity']:>8.0f} | "
                  f"Exit @ ${exit['exit_price']:>8.2f}")
            print(f"           | Proceeds: ${exit['exit_value']:>10,.2f} | "
                  f"P&L: {pnl_sign}${exit['realized_pnl']:>8,.2f} "
                  f"({pnl_sign}{exit['pnl_pct']:>6.2f}%)")
            print()
    
    # Display option exits
    if option_exits:
        print("\n  OPTION EXITS")
        print("  " + "-"*76)
        for exit in option_exits:
            pnl_sign = "+" if exit['realized_pnl'] >= 0 else ""
            position_type = "LONG" if exit['quantity'] > 0 else "SHORT"
            print(f"  {exit['symbol']:20} | {position_type:5} {abs(exit['quantity']):>4.0f} | "
                  f"Exit @ ${exit['exit_price']:>6.2f}")
            print(f"                       | Proceeds: ${exit['exit_value']:>10,.2f} | "
                  f"P&L: {pnl_sign}${exit['realized_pnl']:>8,.2f} "
                  f"({pnl_sign}{exit['pnl_pct']:>6.2f}%)")
            print()
    
    # Calculate post-exit balances
    print("\n" + "="*80)
    print("POST-EXIT ANALYSIS")
    print("="*80)
    
    # Cash after selling all positions
    post_exit_cash = current_cash + total_exit_value
    
    print(f"\n💰 PROJECTED CASH POSITION")
    print(f"  Current Cash:          ${current_cash:,.2f}")
    print(f"  Proceeds from Exits:   ${total_exit_value:,.2f}")
    print(f"  " + "-"*60)
    print(f"  Total Available Cash:  ${post_exit_cash:,.2f}")
    
    print(f"\n📈 REALIZED P&L FROM EXITS")
    pnl_sign = "+" if total_realized_pnl >= 0 else ""
    pnl_pct = (total_realized_pnl / current_nlv * 100) if current_nlv > 0 else 0
    print(f"  Total Realized P&L:    {pnl_sign}${total_realized_pnl:,.2f}")
    print(f"  % of Portfolio:        {pnl_sign}{pnl_pct:.2f}%")
    
    # Position sizing recommendations
    print(f"\n💡 RECOMMENDED POSITION SIZING (Post-Exit)")
    print("-"*80)
    
    # Conservative sizing: 10-15% per position
    max_position_10pct = post_exit_cash * 0.10
    max_position_15pct = post_exit_cash * 0.15
    
    print(f"  10% Position Size:     ${max_position_10pct:,.2f}")
    print(f"  15% Position Size:     ${max_position_15pct:,.2f}")
    print(f"\n  Recommended: 6-8 positions at 10-15% each")
    print(f"  This leaves 20-40% cash buffer for margin and new opportunities")
    
    # Options-specific sizing
    print(f"\n  FOR OPTIONS TRADES:")
    max_option_risk = post_exit_cash * 0.05  # 5% max risk per trade
    print(f"  Max Risk Per Trade:    ${max_option_risk:,.2f} (5% of capital)")
    print(f"  Recommended contracts: Adjust based on max loss not exceeding this")
    
    print("\n" + "="*80)
    
    return {
        'current_cash': current_cash,
        'exit_proceeds': total_exit_value,
        'total_available': post_exit_cash,
        'realized_pnl': total_realized_pnl,
        'max_position_10pct': max_position_10pct,
        'max_position_15pct': max_position_15pct,
        'max_option_risk': max_option_risk
    }


if __name__ == "__main__":
    result = calculate_exit_plan()
