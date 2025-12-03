"""
Portfolio Management Service
============================
Manages user portfolios, positions, and balance tracking.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional


class PortfolioService:
    """
    Manages user portfolios.
    
    Tracks:
    - Cash balance
    - Stock positions
    - Portfolio value
    - P&L calculations
    """
    
    def __init__(self, logger, metrics):
        self.logger = logger
        self.metrics = metrics
        self._portfolios: Dict[str, Dict] = {}
        
    def health_check(self) -> Dict:
        """Check if portfolio service is healthy"""
        return {
            'status': 'healthy',
            'active_portfolios': len(self._portfolios),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _ensure_portfolio(self, user_id: str):
        """Ensure user has a portfolio"""
        if user_id not in self._portfolios:
            self._portfolios[user_id] = {
                'user_id': user_id,
                'cash_balance': 0.0,
                'positions': {},  # symbol -> {quantity, avg_cost}
                'created_at': datetime.utcnow().isoformat()
            }
            self.logger.info(f"[PORTFOLIO] Created new portfolio for {user_id}")
    
    def get_portfolio(self, user_id: str) -> Dict:
        """Get user's complete portfolio"""
        start_time = time.time()
        
        self._ensure_portfolio(user_id)
        portfolio = self._portfolios[user_id]
        
        # Calculate position values (would need current prices in real impl)
        positions_list = []
        for symbol, data in portfolio['positions'].items():
            positions_list.append({
                'symbol': symbol,
                'quantity': data['quantity'],
                'avg_cost': data['avg_cost'],
                'total_cost': data['quantity'] * data['avg_cost']
            })
        
        duration = (time.time() - start_time) * 1000
        self.metrics.record_service_call('PortfolioService', 'get_portfolio', duration, True)
        
        return {
            'user_id': user_id,
            'cash_balance': round(portfolio['cash_balance'], 2),
            'positions': positions_list,
            'created_at': portfolio['created_at']
        }
    
    def set_balance(self, user_id: str, balance: float) -> Dict:
        """Set user's cash balance"""
        start_time = time.time()
        
        self._ensure_portfolio(user_id)
        
        old_balance = self._portfolios[user_id]['cash_balance']
        self._portfolios[user_id]['cash_balance'] = balance
        
        self.logger.info(f"[PORTFOLIO] Balance set for {user_id}: ${old_balance:.2f} -> ${balance:.2f}")
        
        duration = (time.time() - start_time) * 1000
        self.metrics.record_service_call('PortfolioService', 'set_balance', duration, True)
        
        return {
            'success': True,
            'old_balance': old_balance,
            'new_balance': balance
        }
    
    def get_balance(self, user_id: str) -> float:
        """Get user's cash balance"""
        self._ensure_portfolio(user_id)
        return self._portfolios[user_id]['cash_balance']
    
    def add_balance(self, user_id: str, amount: float):
        """Add to user's cash balance"""
        self._ensure_portfolio(user_id)
        self._portfolios[user_id]['cash_balance'] += amount
        self.logger.debug(f"[PORTFOLIO] Added ${amount:.2f} to {user_id}'s balance")
    
    def deduct_balance(self, user_id: str, amount: float) -> bool:
        """Deduct from user's cash balance"""
        self._ensure_portfolio(user_id)
        
        if self._portfolios[user_id]['cash_balance'] < amount:
            self.logger.warning(f"[PORTFOLIO] Insufficient funds for {user_id}: tried to deduct ${amount:.2f}")
            return False
        
        self._portfolios[user_id]['cash_balance'] -= amount
        self.logger.debug(f"[PORTFOLIO] Deducted ${amount:.2f} from {user_id}'s balance")
        return True
    
    def add_position(self, user_id: str, symbol: str, quantity: int, price: float):
        """Add shares to a position"""
        start_time = time.time()
        
        self._ensure_portfolio(user_id)
        positions = self._portfolios[user_id]['positions']
        
        if symbol in positions:
            # Update average cost
            existing = positions[symbol]
            total_shares = existing['quantity'] + quantity
            total_cost = (existing['quantity'] * existing['avg_cost']) + (quantity * price)
            avg_cost = total_cost / total_shares
            
            positions[symbol] = {
                'quantity': total_shares,
                'avg_cost': round(avg_cost, 2)
            }
        else:
            positions[symbol] = {
                'quantity': quantity,
                'avg_cost': round(price, 2)
            }
        
        self.logger.info(
            f"[PORTFOLIO] Position added for {user_id}: {symbol} +{quantity} @ ${price:.2f}"
        )
        
        duration = (time.time() - start_time) * 1000
        self.metrics.record_service_call('PortfolioService', 'add_position', duration, True)
    
    def reduce_position(self, user_id: str, symbol: str, quantity: int) -> bool:
        """Reduce shares in a position"""
        start_time = time.time()
        
        self._ensure_portfolio(user_id)
        positions = self._portfolios[user_id]['positions']
        
        if symbol not in positions:
            self.logger.warning(f"[PORTFOLIO] No position to reduce for {user_id}: {symbol}")
            return False
        
        if positions[symbol]['quantity'] < quantity:
            self.logger.warning(
                f"[PORTFOLIO] Insufficient shares for {user_id}: {symbol} "
                f"(has {positions[symbol]['quantity']}, tried to sell {quantity})"
            )
            return False
        
        positions[symbol]['quantity'] -= quantity
        
        # Remove position if no shares left
        if positions[symbol]['quantity'] == 0:
            del positions[symbol]
            self.logger.info(f"[PORTFOLIO] Position closed for {user_id}: {symbol}")
        else:
            self.logger.info(
                f"[PORTFOLIO] Position reduced for {user_id}: {symbol} -{quantity} "
                f"(remaining: {positions[symbol]['quantity']})"
            )
        
        duration = (time.time() - start_time) * 1000
        self.metrics.record_service_call('PortfolioService', 'reduce_position', duration, True)
        
        return True
    
    def get_position(self, user_id: str, symbol: str) -> Optional[Dict]:
        """Get specific position for user"""
        self._ensure_portfolio(user_id)
        position = self._portfolios[user_id]['positions'].get(symbol)
        
        if position:
            return {
                'symbol': symbol,
                'quantity': position['quantity'],
                'avg_cost': position['avg_cost']
            }
        return None
    
    def get_all_positions(self, user_id: str) -> List[Dict]:
        """Get all positions for user"""
        self._ensure_portfolio(user_id)
        
        positions = []
        for symbol, data in self._portfolios[user_id]['positions'].items():
            positions.append({
                'symbol': symbol,
                'quantity': data['quantity'],
                'avg_cost': data['avg_cost']
            })
        
        return positions
    
    def calculate_portfolio_value(self, user_id: str, current_prices: Dict[str, float]) -> Dict:
        """Calculate total portfolio value with current prices"""
        self._ensure_portfolio(user_id)
        portfolio = self._portfolios[user_id]
        
        positions_value = 0.0
        total_cost = 0.0
        
        for symbol, data in portfolio['positions'].items():
            if symbol in current_prices:
                current_value = data['quantity'] * current_prices[symbol]
                cost_basis = data['quantity'] * data['avg_cost']
                positions_value += current_value
                total_cost += cost_basis
        
        total_value = portfolio['cash_balance'] + positions_value
        unrealized_pnl = positions_value - total_cost
        
        return {
            'cash_balance': portfolio['cash_balance'],
            'positions_value': round(positions_value, 2),
            'total_value': round(total_value, 2),
            'total_cost': round(total_cost, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'unrealized_pnl_pct': round((unrealized_pnl / total_cost * 100) if total_cost > 0 else 0, 2)
        }

