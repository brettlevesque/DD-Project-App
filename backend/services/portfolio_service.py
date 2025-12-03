"""
Portfolio Management Service
============================
Manages user portfolios, positions, and balance tracking.
"""

import time
import traceback
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
        self.logger.info("[PORTFOLIO] PortfolioService initialized")
        
    def health_check(self) -> Dict:
        """Check if portfolio service is healthy"""
        try:
            total_positions = sum(
                len(p.get('positions', {})) 
                for p in self._portfolios.values()
            )
            total_balance = sum(
                p.get('cash_balance', 0) 
                for p in self._portfolios.values()
            )
            
            status = {
                'status': 'healthy',
                'active_portfolios': len(self._portfolios),
                'total_positions': total_positions,
                'total_tracked_balance': round(total_balance, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.debug(f"[PORTFOLIO] Health check: {len(self._portfolios)} portfolios, {total_positions} positions, ${total_balance:.2f} tracked")
            return status
            
        except Exception as e:
            self.logger.error(f"[PORTFOLIO] Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
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
            self.logger.info(f"[PORTFOLIO] Created new portfolio for user: {user_id} | total_portfolios: {len(self._portfolios)}")
        else:
            self.logger.debug(f"[PORTFOLIO] Portfolio exists for user: {user_id}")
    
    def get_portfolio(self, user_id: str) -> Dict:
        """Get user's complete portfolio"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[PORTFOLIO] Fetching portfolio for user: {user_id}")
            
            self._ensure_portfolio(user_id)
            portfolio = self._portfolios[user_id]
            
            # Calculate position values (would need current prices in real impl)
            positions_list = []
            total_cost_basis = 0.0
            
            for symbol, data in portfolio['positions'].items():
                position_cost = data['quantity'] * data['avg_cost']
                total_cost_basis += position_cost
                positions_list.append({
                    'symbol': symbol,
                    'quantity': data['quantity'],
                    'avg_cost': data['avg_cost'],
                    'total_cost': round(position_cost, 2)
                })
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.debug(f"[PORTFOLIO] Portfolio retrieved: user={user_id} | cash=${portfolio['cash_balance']:.2f} | positions={len(positions_list)} | cost_basis=${total_cost_basis:.2f} | {duration:.2f}ms")
            self.metrics.record_service_call('PortfolioService', 'get_portfolio', duration, True)
            
            return {
                'user_id': user_id,
                'cash_balance': round(portfolio['cash_balance'], 2),
                'positions': positions_list,
                'created_at': portfolio['created_at']
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[PORTFOLIO] Failed to get portfolio for {user_id}: {str(e)} | {duration:.2f}ms")
            self.logger.error(f"[PORTFOLIO] Traceback: {traceback.format_exc()}")
            self.metrics.record_service_call('PortfolioService', 'get_portfolio', duration, False)
            raise
    
    def set_balance(self, user_id: str, balance: float) -> Dict:
        """Set user's cash balance"""
        start_time = time.time()
        
        try:
            self._ensure_portfolio(user_id)
            
            old_balance = self._portfolios[user_id]['cash_balance']
            self._portfolios[user_id]['cash_balance'] = balance
            change = balance - old_balance
            
            self.logger.info(f"[PORTFOLIO] Balance SET: user={user_id} | ${old_balance:.2f} -> ${balance:.2f} | change: ${change:+.2f}")
            
            duration = (time.time() - start_time) * 1000
            self.metrics.record_service_call('PortfolioService', 'set_balance', duration, True)
            
            return {
                'success': True,
                'old_balance': old_balance,
                'new_balance': balance,
                'change': change
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[PORTFOLIO] Failed to set balance for {user_id}: {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('PortfolioService', 'set_balance', duration, False)
            return {'success': False, 'error': str(e)}
    
    def get_balance(self, user_id: str) -> float:
        """Get user's cash balance"""
        self._ensure_portfolio(user_id)
        balance = self._portfolios[user_id]['cash_balance']
        self.logger.debug(f"[PORTFOLIO] Balance inquiry: user={user_id} | balance=${balance:.2f}")
        return balance
    
    def add_balance(self, user_id: str, amount: float):
        """Add to user's cash balance"""
        try:
            self._ensure_portfolio(user_id)
            old_balance = self._portfolios[user_id]['cash_balance']
            self._portfolios[user_id]['cash_balance'] += amount
            new_balance = self._portfolios[user_id]['cash_balance']
            self.logger.info(f"[PORTFOLIO] Balance ADDED: user={user_id} | ${old_balance:.2f} + ${amount:.2f} = ${new_balance:.2f}")
        except Exception as e:
            self.logger.error(f"[PORTFOLIO] Failed to add balance for {user_id}: {str(e)}")
            raise
    
    def deduct_balance(self, user_id: str, amount: float) -> bool:
        """Deduct from user's cash balance"""
        try:
            self._ensure_portfolio(user_id)
            
            current = self._portfolios[user_id]['cash_balance']
            
            if current < amount:
                shortfall = amount - current
                self.logger.warning(f"[PORTFOLIO] Balance DEDUCTION FAILED: user={user_id} | current=${current:.2f} | requested=${amount:.2f} | shortfall=${shortfall:.2f}")
                return False
            
            self._portfolios[user_id]['cash_balance'] -= amount
            new_balance = self._portfolios[user_id]['cash_balance']
            self.logger.info(f"[PORTFOLIO] Balance DEDUCTED: user={user_id} | ${current:.2f} - ${amount:.2f} = ${new_balance:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"[PORTFOLIO] Failed to deduct balance for {user_id}: {str(e)}")
            return False
    
    def add_position(self, user_id: str, symbol: str, quantity: int, price: float):
        """Add shares to a position"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[PORTFOLIO] Adding position: user={user_id} | symbol={symbol} | qty={quantity} | price=${price:.2f}")
            
            self._ensure_portfolio(user_id)
            positions = self._portfolios[user_id]['positions']
            
            if symbol in positions:
                # Update average cost
                existing = positions[symbol]
                old_qty = existing['quantity']
                old_avg = existing['avg_cost']
                
                total_shares = old_qty + quantity
                total_cost = (old_qty * old_avg) + (quantity * price)
                avg_cost = total_cost / total_shares
                
                positions[symbol] = {
                    'quantity': total_shares,
                    'avg_cost': round(avg_cost, 2)
                }
                
                self.logger.info(f"[PORTFOLIO] Position INCREASED: user={user_id} | symbol={symbol}")
                self.logger.info(f"[PORTFOLIO]   Shares: {old_qty} + {quantity} = {total_shares}")
                self.logger.info(f"[PORTFOLIO]   Avg Cost: ${old_avg:.2f} -> ${avg_cost:.2f}")
            else:
                positions[symbol] = {
                    'quantity': quantity,
                    'avg_cost': round(price, 2)
                }
                self.logger.info(f"[PORTFOLIO] Position OPENED: user={user_id} | symbol={symbol} | qty={quantity} | avg_cost=${price:.2f}")
            
            total_positions = len(positions)
            duration = (time.time() - start_time) * 1000
            
            self.logger.debug(f"[PORTFOLIO] Position added successfully | user_positions={total_positions} | {duration:.2f}ms")
            self.metrics.record_service_call('PortfolioService', 'add_position', duration, True)
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[PORTFOLIO] Failed to add position for {user_id}: {str(e)} | {duration:.2f}ms")
            self.logger.error(f"[PORTFOLIO] Traceback: {traceback.format_exc()}")
            self.metrics.record_service_call('PortfolioService', 'add_position', duration, False)
            raise
    
    def reduce_position(self, user_id: str, symbol: str, quantity: int) -> bool:
        """Reduce shares in a position"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[PORTFOLIO] Reducing position: user={user_id} | symbol={symbol} | qty={quantity}")
            
            self._ensure_portfolio(user_id)
            positions = self._portfolios[user_id]['positions']
            
            if symbol not in positions:
                self.logger.warning(f"[PORTFOLIO] Position REDUCTION FAILED: user={user_id} | symbol={symbol} | reason=no_position_exists")
                return False
            
            current_qty = positions[symbol]['quantity']
            avg_cost = positions[symbol]['avg_cost']
            
            if current_qty < quantity:
                self.logger.warning(f"[PORTFOLIO] Position REDUCTION FAILED: user={user_id} | symbol={symbol}")
                self.logger.warning(f"[PORTFOLIO]   Current shares: {current_qty} | Requested: {quantity} | Shortfall: {quantity - current_qty}")
                return False
            
            positions[symbol]['quantity'] -= quantity
            remaining = positions[symbol]['quantity']
            
            # Remove position if no shares left
            if remaining == 0:
                del positions[symbol]
                self.logger.info(f"[PORTFOLIO] Position CLOSED: user={user_id} | symbol={symbol} | sold_qty={quantity} | avg_cost=${avg_cost:.2f}")
            else:
                self.logger.info(f"[PORTFOLIO] Position REDUCED: user={user_id} | symbol={symbol}")
                self.logger.info(f"[PORTFOLIO]   Shares: {current_qty} - {quantity} = {remaining}")
            
            duration = (time.time() - start_time) * 1000
            self.metrics.record_service_call('PortfolioService', 'reduce_position', duration, True)
            
            return True
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[PORTFOLIO] Failed to reduce position for {user_id}: {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('PortfolioService', 'reduce_position', duration, False)
            return False
    
    def get_position(self, user_id: str, symbol: str) -> Optional[Dict]:
        """Get specific position for user"""
        try:
            self._ensure_portfolio(user_id)
            position = self._portfolios[user_id]['positions'].get(symbol)
            
            if position:
                self.logger.debug(f"[PORTFOLIO] Position found: user={user_id} | symbol={symbol} | qty={position['quantity']} | avg_cost=${position['avg_cost']:.2f}")
                return {
                    'symbol': symbol,
                    'quantity': position['quantity'],
                    'avg_cost': position['avg_cost']
                }
            
            self.logger.debug(f"[PORTFOLIO] Position not found: user={user_id} | symbol={symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"[PORTFOLIO] Error getting position for {user_id}/{symbol}: {str(e)}")
            return None
    
    def get_all_positions(self, user_id: str) -> List[Dict]:
        """Get all positions for user"""
        try:
            self._ensure_portfolio(user_id)
            
            positions = []
            total_cost_basis = 0.0
            
            for symbol, data in self._portfolios[user_id]['positions'].items():
                cost_basis = data['quantity'] * data['avg_cost']
                total_cost_basis += cost_basis
                positions.append({
                    'symbol': symbol,
                    'quantity': data['quantity'],
                    'avg_cost': data['avg_cost']
                })
            
            self.logger.debug(f"[PORTFOLIO] All positions retrieved: user={user_id} | positions={len(positions)} | total_cost_basis=${total_cost_basis:.2f}")
            return positions
            
        except Exception as e:
            self.logger.error(f"[PORTFOLIO] Error getting all positions for {user_id}: {str(e)}")
            return []
    
    def calculate_portfolio_value(self, user_id: str, current_prices: Dict[str, float]) -> Dict:
        """Calculate total portfolio value with current prices"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[PORTFOLIO] Calculating portfolio value for user: {user_id}")
            
            self._ensure_portfolio(user_id)
            portfolio = self._portfolios[user_id]
            
            positions_value = 0.0
            total_cost = 0.0
            position_details = []
            
            for symbol, data in portfolio['positions'].items():
                if symbol in current_prices:
                    current_value = data['quantity'] * current_prices[symbol]
                    cost_basis = data['quantity'] * data['avg_cost']
                    pnl = current_value - cost_basis
                    pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                    
                    positions_value += current_value
                    total_cost += cost_basis
                    
                    position_details.append(f"{symbol}: ${current_value:.2f} (P&L: ${pnl:+.2f} / {pnl_pct:+.1f}%)")
                else:
                    self.logger.warning(f"[PORTFOLIO] No price available for {symbol}, using cost basis")
                    cost_basis = data['quantity'] * data['avg_cost']
                    positions_value += cost_basis
                    total_cost += cost_basis
            
            total_value = portfolio['cash_balance'] + positions_value
            unrealized_pnl = positions_value - total_cost
            unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.debug(f"[PORTFOLIO] Portfolio value calculated: user={user_id}")
            self.logger.debug(f"[PORTFOLIO]   Cash: ${portfolio['cash_balance']:.2f}")
            self.logger.debug(f"[PORTFOLIO]   Positions: ${positions_value:.2f}")
            self.logger.debug(f"[PORTFOLIO]   Total: ${total_value:.2f}")
            self.logger.debug(f"[PORTFOLIO]   Unrealized P&L: ${unrealized_pnl:+.2f} ({unrealized_pnl_pct:+.1f}%)")
            self.logger.debug(f"[PORTFOLIO]   Calculation time: {duration:.2f}ms")
            
            return {
                'cash_balance': portfolio['cash_balance'],
                'positions_value': round(positions_value, 2),
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'unrealized_pnl': round(unrealized_pnl, 2),
                'unrealized_pnl_pct': round(unrealized_pnl_pct, 2)
            }
            
        except Exception as e:
            self.logger.error(f"[PORTFOLIO] Error calculating portfolio value for {user_id}: {str(e)}")
            self.logger.error(f"[PORTFOLIO] Traceback: {traceback.format_exc()}")
            return {
                'cash_balance': 0,
                'positions_value': 0,
                'total_value': 0,
                'total_cost': 0,
                'unrealized_pnl': 0,
                'unrealized_pnl_pct': 0,
                'error': str(e)
            }

