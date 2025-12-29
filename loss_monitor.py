"""
Loss Monitor - Advises on early exits when positions go against you
"""

from tastytrade_client import TastytradeClient
from datetime import datetime
from typing import List, Dict


def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


class LossMonitor:
    """Monitor positions and recommend stops for losers."""
    
    def __init__(self):
        self.client = TastytradeClient()
        
        # Stop loss rules (configurable)
        self.rules = {
            'max_loss_pct': 100,      # Exit if loss > 100% of credit (2x max loss)
            'max_loss_multiple': 2.0,  # Exit if loss > 2x credit received
            'time_stop_days': 21,      # Exit if losing after 21 days (75% of 30 DTE)
            'delta_warning': 0.50,     # Warn if delta moves against you significantly
        }
    
    def check_positions(self, account_number: str) -> Dict:
        """
        Check all positions for stop loss conditions.
        
        Args:
            account_number: Account to check
            
        Returns:
            Dict with warnings and recommendations
        """
        print(f"\n{'='*80}")
        print(f"LOSS MONITOR - Position Health Check")
        print(f"Account: {account_number}")
        print(f"{'='*80}\n")
        
        positions = self.client.get_positions(account_number)
        
        if not positions:
            print("  ℹ️  No open positions")
            return {'warnings': [], 'recommendations': []}
        
        warnings = []
        recommendations = []
        healthy_positions = []
        
        for pos in positions:
            symbol = pos.get('symbol', 'N/A')
            quantity = safe_float(pos.get('quantity'))
            
            # Only monitor options for now
            inst_type = pos.get('instrument-type', '').lower()
            if 'option' not in inst_type:
                continue
            
            # Calculate P&L
            avg_price = safe_float(pos.get('average-open-price'))
            current_price = safe_float(pos.get('close-price'))
            multiplier = safe_float(pos.get('multiplier', 100))
            
            # For credit spreads, we sold (short position)
            # P&L = (entry_credit - current_debit) * multiplier * contracts
            if quantity < 0:  # Short position (we sold)
                # Entry credit was positive (we collected money)
                entry_credit = avg_price
                current_debit = current_price
                unrealized_pnl = (entry_credit - current_debit) * abs(quantity) * multiplier
                
                # Loss threshold: if we're losing more than 2x the credit we received
                max_loss = entry_credit * abs(quantity) * multiplier * self.rules['max_loss_multiple']
                loss_pct = (unrealized_pnl / (entry_credit * abs(quantity) * multiplier)) * 100
                
            else:  # Long position (we bought)
                cost_basis = avg_price * quantity * multiplier
                current_value = current_price * quantity * multiplier
                unrealized_pnl = current_value - cost_basis
                max_loss = cost_basis * 0.5  # 50% of investment
                loss_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
            
            # Check stop loss conditions
            if unrealized_pnl < 0:  # Losing position
                severity = self._assess_severity(unrealized_pnl, max_loss, loss_pct)
                
                if severity in ['CRITICAL', 'WARNING']:
                    warnings.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'unrealized_pnl': unrealized_pnl,
                        'loss_pct': loss_pct,
                        'severity': severity,
                        'current_price': current_price,
                        'avg_price': avg_price
                    })
                    
                    # Generate recommendation
                    rec = self._generate_recommendation(
                        symbol, quantity, unrealized_pnl, loss_pct, severity
                    )
                    recommendations.append(rec)
            else:
                healthy_positions.append({
                    'symbol': symbol,
                    'unrealized_pnl': unrealized_pnl,
                    'profit_pct': loss_pct
                })
        
        # Display results
        if warnings:
            print(f"⚠️  ALERT: {len(warnings)} position(s) need attention!\n")
            print("-" * 80)
            
            for warning in warnings:
                self._display_warning(warning)
        else:
            print(f"✓ All {len(positions)} positions are healthy")
        
        if healthy_positions:
            print(f"\n📊 HEALTHY POSITIONS ({len(healthy_positions)}):")
            for pos in healthy_positions[:5]:  # Show top 5
                print(f"  {pos['symbol']:20} | P&L: ${pos['unrealized_pnl']:>8,.2f} "
                      f"({pos['profit_pct']:>+6.1f}%)")
        
        return {
            'warnings': warnings,
            'recommendations': recommendations,
            'healthy_count': len(healthy_positions)
        }
    
    def _assess_severity(self, pnl: float, max_loss: float, loss_pct: float) -> str:
        """Determine severity of loss."""
        
        # CRITICAL: Loss exceeds 2x max or 100%+
        if abs(pnl) > abs(max_loss) or loss_pct < -100:
            return 'CRITICAL'
        
        # WARNING: Loss > 50% or significant
        elif loss_pct < -50 or abs(pnl) > (abs(max_loss) * 0.5):
            return 'WARNING'
        
        # WATCH: Small loss, monitor
        elif loss_pct < -25:
            return 'WATCH'
        
        return 'OK'
    
    def _generate_recommendation(self, symbol: str, quantity: float, 
                                 pnl: float, loss_pct: float, severity: str) -> Dict:
        """Generate exit recommendation."""
        
        if severity == 'CRITICAL':
            action = "EXIT IMMEDIATELY"
            reason = "Loss has exceeded acceptable threshold (>2x max loss)"
            urgency = "🚨 URGENT"
        
        elif severity == 'WARNING':
            action = "CONSIDER EXITING"
            reason = "Position is significantly underwater (>50% loss)"
            urgency = "⚠️  HIGH"
        
        else:  # WATCH
            action = "MONITOR CLOSELY"
            reason = "Position showing moderate loss"
            urgency = "📊 MEDIUM"
        
        return {
            'symbol': symbol,
            'quantity': quantity,
            'pnl': pnl,
            'loss_pct': loss_pct,
            'action': action,
            'reason': reason,
            'urgency': urgency,
            'severity': severity
        }
    
    def _display_warning(self, warning: Dict):
        """Display position warning."""
        
        severity_icon = {
            'CRITICAL': '🚨',
            'WARNING': '⚠️ ',
            'WATCH': '📊'
        }.get(warning['severity'], '❓')
        
        print(f"\n{severity_icon} {warning['severity']}: {warning['symbol']}")
        print(f"  Position:     {abs(warning['quantity']):.0f} contracts")
        print(f"  Current P&L:  ${warning['unrealized_pnl']:,.2f} ({warning['loss_pct']:+.1f}%)")
        print(f"  Current:      ${warning['current_price']:.2f}")
        print(f"  Entry:        ${warning['avg_price']:.2f}")
        
        # Get recommendation
        if warning['severity'] == 'CRITICAL':
            print(f"\n  ACTION: 🚨 EXIT IMMEDIATELY")
            print(f"  REASON: Loss exceeds 2x max acceptable loss")
            print(f"  EXECUTE: Close this position today")
        
        elif warning['severity'] == 'WARNING':
            print(f"\n  ACTION: ⚠️  STRONGLY CONSIDER EXITING")
            print(f"  REASON: Significant unrealized loss (>50%)")
            print(f"  EXECUTE: Exit within 1-2 days or set hard stop")
        
        else:  # WATCH
            print(f"\n  ACTION: 📊 MONITOR CLOSELY")
            print(f"  REASON: Moderate loss - watch for further deterioration")
            print(f"  EXECUTE: Set mental stop at -50%")
        
        print("-" * 80)
    
    def generate_exit_report(self, warnings: List[Dict]) -> str:
        """Generate detailed exit recommendations report."""
        
        if not warnings:
            return "No positions require exits at this time."
        
        report = []
        report.append("="*80)
        report.append("POSITION EXIT RECOMMENDATIONS")
        report.append("="*80)
        report.append("")
        
        # Group by severity
        critical = [w for w in warnings if w['severity'] == 'CRITICAL']
        warning = [w for w in warnings if w['severity'] == 'WARNING']
        watch = [w for w in warnings if w['severity'] == 'WATCH']
        
        if critical:
            report.append("🚨 CRITICAL - EXIT TODAY:")
            report.append("-" * 80)
            for w in critical:
                report.append(f"{w['symbol']:15} | Loss: ${w['unrealized_pnl']:>10,.2f} ({w['loss_pct']:>+6.1f}%)")
                report.append(f"{'':15} | Action: Close immediately - loss too large")
                report.append("")
        
        if warning:
            report.append("\n⚠️  WARNING - EXIT SOON:")
            report.append("-" * 80)
            for w in warning:
                report.append(f"{w['symbol']:15} | Loss: ${w['unrealized_pnl']:>10,.2f} ({w['loss_pct']:>+6.1f}%)")
                report.append(f"{'':15} | Action: Exit within 1-2 days")
                report.append("")
        
        if watch:
            report.append("\n📊 WATCH - MONITOR:")
            report.append("-" * 80)
            for w in watch:
                report.append(f"{w['symbol']:15} | Loss: ${w['unrealized_pnl']:>10,.2f} ({w['loss_pct']:>+6.1f}%)")
                report.append(f"{'':15} | Action: Set stop at -50%")
                report.append("")
        
        report.append("="*80)
        report.append("\nGENERAL RULES:")
        report.append("  • Cut losers quickly - don't let hope turn into disaster")
        report.append("  • Accept small losses to preserve capital")
        report.append("  • Never let a winner turn into a loser")
        report.append("  • Remember: You can always re-enter if thesis still valid")
        report.append("="*80)
        
        return "\n".join(report)


if __name__ == "__main__":
    monitor = LossMonitor()
    
    # Get accounts
    client = TastytradeClient()
    accounts = client.get_account_numbers()
    
    if accounts:
        results = monitor.check_positions(accounts[0])
        
        if results['warnings']:
            print("\n" + monitor.generate_exit_report(results['warnings']))
