"""
Position Sizing Calculator
Calculates optimal contract quantities based on account size and risk tolerance.
"""


class PositionSizer:
    """Calculate position sizes for options trades."""
    
    def __init__(self, account_size, max_risk_per_trade=0.05):
        """
        Initialize position sizer.
        
        Args:
            account_size: Total account value
            max_risk_per_trade: Maximum % of account to risk per trade (default 5%)
        """
        self.account_size = account_size
        self.max_risk_per_trade = max_risk_per_trade
        self.max_risk_dollars = account_size * max_risk_per_trade
    
    def size_credit_spread(self, width, credit_per_spread):
        """
        Calculate contracts for a credit spread.
        
        Args:
            width: Dollar width of spread
            credit_per_spread: Credit received per spread (in dollars)
            
        Returns:
            Number of contracts to trade
        """
        max_loss_per_spread = (width - credit_per_spread) * 100
        
        if max_loss_per_spread <= 0:
            return 0
        
        # Calculate contracts based on max risk
        contracts = int(self.max_risk_dollars / max_loss_per_spread)
        
        # Ensure at least 1 contract if spread meets criteria
        if contracts == 0 and credit_per_spread >= (width / 3):
            contracts = 1
        
        return contracts
    
    def calculate_position_details(self, opportunity, contracts=None):
        """
        Calculate full position details.
        
        Args:
            opportunity: Dict with trade details
            contracts: Number of contracts (if None, will auto-calculate)
            
        Returns:
            Dict with position sizing details
        """
        width = opportunity.get('width', 0)
        credit = opportunity.get('credit', 0)
        
        if contracts is None:
            contracts = self.size_credit_spread(width, credit)
        
        max_loss_per_spread = (width - credit) * 100
        total_max_loss = max_loss_per_spread * contracts
        total_credit = credit * 100 * contracts
        total_risk_pct = (total_max_loss / self.account_size) * 100
        
        return {
            'contracts': contracts,
            'total_credit': total_credit,
            'total_max_loss': total_max_loss,
            'risk_pct': total_risk_pct,
            'meets_criteria': contracts > 0 and total_risk_pct <= (self.max_risk_per_trade * 100)
        }
    
    def format_trade_recommendation(self, opportunity, sizing):
        """Format a trade recommendation with sizing."""
        symbol = opportunity.get('symbol', 'N/A')
        strategy = opportunity.get('strategy', 'N/A')
        expiration = opportunity.get('expiration', 'N/A')
        dte = opportunity.get('dte', 0)
        short_strike = opportunity.get('short_strike', 0)
        long_strike = opportunity.get('long_strike', 0)
        
        contracts = sizing['contracts']
        total_credit = sizing['total_credit']
        total_max_loss = sizing['total_max_loss']
        risk_pct = sizing['risk_pct']
        
        rec = f"""
{'='*80}
TRADE RECOMMENDATION: {symbol}
{'='*80}

Strategy: {strategy}
Expiration: {expiration} ({dte} days)

ENTRY:
  Sell  {contracts} x ${short_strike:.2f} Put
  Buy   {contracts} x ${long_strike:.2f} Put
  
  Target Credit: ${total_credit:.0f} total (${opportunity.get('credit', 0):.2f} per spread)
  
RISK/REWARD:
  Max Profit:    ${total_credit:.0f}
  Max Loss:      ${total_max_loss:.0f}
  Account Risk:  {risk_pct:.2f}% (targeting <5%)
  Return on Risk: {opportunity.get('return_on_risk', 0):.1f}%
  
PROBABILITY:
  Probability of Profit: ~{opportunity.get('pop', 0):.0f}%
  
MANAGEMENT:
  - Close at 50% of max profit (${total_credit * 0.5:.0f})
  - Set stop loss at 2x credit received
  - Monitor daily for changes in IV rank

WHY THIS TRADE:
  - IV Rank: {opportunity.get('iv_rank', 0):.1f}% (premium is expensive)
  - High probability setup (~{opportunity.get('pop', 0):.0f}% chance of profit)
  - Theta decay working in your favor
  - Credit > 1/3 of width (good risk/reward)

{'='*80}
"""
        return rec


if __name__ == "__main__":
    # Example usage
    sizer = PositionSizer(account_size=46000, max_risk_per_trade=0.05)
    
    # Example opportunity
    example_opp = {
        'symbol': 'SPY',
        'strategy': 'Put Credit Spread',
        'expiration': '2026-02-20',
        'dte': 57,
        'short_strike': 565,
        'long_strike': 560,
        'width': 5,
        'credit': 1.75,
        'iv_rank': 65.5,
        'pop': 70,
        'return_on_risk': 35
    }
    
    sizing = sizer.calculate_position_details(example_opp)
    print(sizer.format_trade_recommendation(example_opp, sizing))
