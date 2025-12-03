"""
Trade Execution Service
=======================
Simulates trade processing with realistic delays and occasional failures.

Demonstrates:
- Complex operation timing
- Error tracking
- Transaction logging
"""

import time
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional


class TradeService:
    """
    Handles trade execution and order management.
    
    In a real system, this would:
    - Connect to exchange APIs
    - Manage order books
    - Handle partial fills
    - Process settlements
    """
    
    def __init__(self, logger, metrics):
        self.logger = logger
        self.metrics = metrics
        self._trades: Dict[str, List[Dict]] = {}  # user_id -> trades
        self._pending_orders: Dict[str, Dict] = {}
        
        # Simulate occasional failures
        self._failure_rate = 0.02  # 2% failure rate
        
    def health_check(self) -> Dict:
        """Check if trade service is healthy"""
        # Simulate checking connection to exchange
        time.sleep(random.uniform(0.01, 0.03))
        
        return {
            'status': 'healthy',
            'pending_orders': len(self._pending_orders),
            'total_trades': sum(len(t) for t in self._trades.values()),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def execute_trade(self, user_id: str, symbol: str, quantity: int, 
                      price: float, side: str) -> Dict:
        """
        Execute a trade order.
        
        This simulates the multi-step process of:
        1. Order validation
        2. Exchange submission
        3. Fill confirmation
        4. Settlement
        """
        start_time = time.time()
        trade_id = str(uuid.uuid4())[:8]
        
        self.logger.info(f"[TRADE] Processing {side} order: {trade_id} | {symbol} x {quantity} @ ${price}")
        
        try:
            # Step 1: Validate order (fast)
            self._validate_order(symbol, quantity, price)
            
            # Step 2: Submit to exchange (simulate network latency)
            self._submit_to_exchange(trade_id, symbol, quantity, price, side)
            
            # Step 3: Wait for fill confirmation
            fill_result = self._wait_for_fill(trade_id)
            
            if not fill_result['filled']:
                raise Exception(f"Order not filled: {fill_result['reason']}")
            
            # Step 4: Process settlement
            self._process_settlement(trade_id, user_id)
            
            # Create trade record
            trade = {
                'trade_id': trade_id,
                'user_id': user_id,
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'side': side,
                'total_value': price * quantity,
                'status': 'completed',
                'executed_at': datetime.utcnow().isoformat(),
                'fees': round(price * quantity * 0.001, 2)  # 0.1% fee
            }
            
            # Store trade
            if user_id not in self._trades:
                self._trades[user_id] = []
            self._trades[user_id].append(trade)
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"[TRADE] Completed: {trade_id} | {side} {symbol} x {quantity} @ ${price} | "
                f"Total: ${trade['total_value']:.2f} | {duration:.2f}ms"
            )
            
            self.metrics.record_trade(trade['total_value'])
            self.metrics.record_service_call('TradeService', 'execute_trade', duration, True)
            
            return {
                'success': True,
                'trade': trade
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"[TRADE] Failed: {trade_id} | {side} {symbol} x {quantity} @ ${price} | "
                f"Error: {str(e)} | {duration:.2f}ms"
            )
            
            self.metrics.record_service_call('TradeService', 'execute_trade', duration, False)
            
            return {
                'success': False,
                'error': str(e),
                'trade_id': trade_id
            }
    
    def _validate_order(self, symbol: str, quantity: int, price: float):
        """Validate order parameters"""
        time.sleep(random.uniform(0.01, 0.02))
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price <= 0:
            raise ValueError("Price must be positive")
        if quantity > 10000:
            raise ValueError("Order exceeds maximum quantity (10000)")
    
    def _submit_to_exchange(self, trade_id: str, symbol: str, 
                            quantity: int, price: float, side: str):
        """Simulate submitting order to exchange"""
        # Simulate network latency to exchange
        latency = random.uniform(0.1, 0.3)
        time.sleep(latency)
        
        self.logger.debug(f"[TRADE] Order {trade_id} submitted to exchange | latency: {latency*1000:.0f}ms")
        
        # Simulate occasional exchange errors
        if random.random() < self._failure_rate:
            raise Exception("Exchange connection timeout")
        
        self._pending_orders[trade_id] = {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'side': side,
            'submitted_at': datetime.utcnow().isoformat()
        }
    
    def _wait_for_fill(self, trade_id: str) -> Dict:
        """Wait for order to be filled"""
        # Simulate waiting for fill
        fill_time = random.uniform(0.05, 0.2)
        time.sleep(fill_time)
        
        # Simulate occasional partial fills or rejections
        if random.random() < self._failure_rate:
            return {'filled': False, 'reason': 'Market moved, order rejected'}
        
        self.logger.debug(f"[TRADE] Order {trade_id} filled | fill_time: {fill_time*1000:.0f}ms")
        
        if trade_id in self._pending_orders:
            del self._pending_orders[trade_id]
        
        return {'filled': True}
    
    def _process_settlement(self, trade_id: str, user_id: str):
        """Process trade settlement"""
        # Simulate settlement processing
        time.sleep(random.uniform(0.02, 0.05))
        
        self.logger.debug(f"[TRADE] Settlement processed for {trade_id}")
    
    def get_trade_history(self, user_id: str) -> List[Dict]:
        """Get user's trade history"""
        start_time = time.time()
        
        trades = self._trades.get(user_id, [])
        
        duration = (time.time() - start_time) * 1000
        self.metrics.record_service_call('TradeService', 'get_trade_history', duration, True)
        
        return trades
    
    def get_pending_orders(self, user_id: str) -> List[Dict]:
        """Get user's pending orders"""
        # Filter pending orders for user (simplified - in reality would be indexed)
        return [
            {'trade_id': tid, **order} 
            for tid, order in self._pending_orders.items()
        ]

