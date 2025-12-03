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
import traceback
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
        
        self.logger.info(f"[TRADE] TradeService initialized | failure_rate: {self._failure_rate*100:.1f}%")
        
    def health_check(self) -> Dict:
        """Check if trade service is healthy"""
        start_time = time.time()
        
        try:
            # Simulate checking connection to exchange
            latency = random.uniform(0.01, 0.03)
            time.sleep(latency)
            
            total_trades = sum(len(t) for t in self._trades.values())
            total_users = len(self._trades)
            
            status = {
                'status': 'healthy',
                'pending_orders': len(self._pending_orders),
                'total_trades': total_trades,
                'total_users': total_users,
                'exchange_latency_ms': round(latency * 1000, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            duration = (time.time() - start_time) * 1000
            self.logger.debug(f"[TRADE] Health check completed: {total_trades} trades, {len(self._pending_orders)} pending | {duration:.2f}ms")
            
            return status
            
        except Exception as e:
            self.logger.error(f"[TRADE] Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
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
        total_value = price * quantity
        
        self.logger.info(f"[TRADE] ========== TRADE EXECUTION START ==========")
        self.logger.info(f"[TRADE] Processing {side.upper()} order: {trade_id}")
        self.logger.info(f"[TRADE] Order details: user={user_id} | symbol={symbol} | qty={quantity} | price=${price:.2f} | total=${total_value:.2f}")
        
        try:
            # Step 1: Validate order (fast)
            self.logger.debug(f"[TRADE] Step 1/4: Validating order {trade_id}...")
            validation_start = time.time()
            self._validate_order(symbol, quantity, price)
            validation_time = (time.time() - validation_start) * 1000
            self.logger.debug(f"[TRADE] Step 1/4: Order validation passed | {validation_time:.2f}ms")
            
            # Step 2: Submit to exchange (simulate network latency)
            self.logger.debug(f"[TRADE] Step 2/4: Submitting order {trade_id} to exchange...")
            submit_start = time.time()
            self._submit_to_exchange(trade_id, symbol, quantity, price, side)
            submit_time = (time.time() - submit_start) * 1000
            self.logger.debug(f"[TRADE] Step 2/4: Order submitted to exchange | {submit_time:.2f}ms")
            
            # Step 3: Wait for fill confirmation
            self.logger.debug(f"[TRADE] Step 3/4: Waiting for fill confirmation {trade_id}...")
            fill_start = time.time()
            fill_result = self._wait_for_fill(trade_id)
            fill_time = (time.time() - fill_start) * 1000
            
            if not fill_result['filled']:
                self.logger.warning(f"[TRADE] Step 3/4: Order NOT filled: {fill_result['reason']} | {fill_time:.2f}ms")
                raise Exception(f"Order not filled: {fill_result['reason']}")
            self.logger.debug(f"[TRADE] Step 3/4: Order filled | {fill_time:.2f}ms")
            
            # Step 4: Process settlement
            self.logger.debug(f"[TRADE] Step 4/4: Processing settlement for {trade_id}...")
            settle_start = time.time()
            self._process_settlement(trade_id, user_id)
            settle_time = (time.time() - settle_start) * 1000
            self.logger.debug(f"[TRADE] Step 4/4: Settlement complete | {settle_time:.2f}ms")
            
            # Create trade record
            fees = round(total_value * 0.001, 2)  # 0.1% fee
            trade = {
                'trade_id': trade_id,
                'user_id': user_id,
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'side': side,
                'total_value': total_value,
                'status': 'completed',
                'executed_at': datetime.utcnow().isoformat(),
                'fees': fees
            }
            
            # Store trade
            if user_id not in self._trades:
                self._trades[user_id] = []
                self.logger.debug(f"[TRADE] Created new trade history for user: {user_id}")
            self._trades[user_id].append(trade)
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.info(f"[TRADE] ✓ TRADE COMPLETED: {trade_id}")
            self.logger.info(f"[TRADE] Summary: {side.upper()} {quantity} {symbol} @ ${price:.2f} = ${total_value:.2f} (fees: ${fees:.2f})")
            self.logger.info(f"[TRADE] Timing breakdown: validate={validation_time:.0f}ms, submit={submit_time:.0f}ms, fill={fill_time:.0f}ms, settle={settle_time:.0f}ms")
            self.logger.info(f"[TRADE] Total execution time: {duration:.2f}ms | user_total_trades: {len(self._trades[user_id])}")
            self.logger.info(f"[TRADE] ========== TRADE EXECUTION END ==========")
            
            self.metrics.record_trade(trade['total_value'])
            self.metrics.record_service_call('TradeService', 'execute_trade', duration, True)
            
            return {
                'success': True,
                'trade': trade
            }
            
        except ValueError as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[TRADE] ✗ VALIDATION ERROR: {trade_id} | {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('TradeService', 'execute_trade', duration, False)
            return {
                'success': False,
                'error': str(e),
                'trade_id': trade_id,
                'error_type': 'validation'
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[TRADE] ✗ TRADE FAILED: {trade_id}")
            self.logger.error(f"[TRADE] Error: {str(e)}")
            self.logger.error(f"[TRADE] Details: {side.upper()} {quantity} {symbol} @ ${price:.2f} | {duration:.2f}ms")
            self.logger.error(f"[TRADE] Traceback: {traceback.format_exc()}")
            self.logger.info(f"[TRADE] ========== TRADE EXECUTION END (FAILED) ==========")
            
            self.metrics.record_service_call('TradeService', 'execute_trade', duration, False)
            
            return {
                'success': False,
                'error': str(e),
                'trade_id': trade_id
            }
    
    def _validate_order(self, symbol: str, quantity: int, price: float):
        """Validate order parameters"""
        validation_delay = random.uniform(0.01, 0.02)
        time.sleep(validation_delay)
        
        self.logger.debug(f"[TRADE] Validating: symbol={symbol}, quantity={quantity}, price=${price:.2f}")
        
        if quantity <= 0:
            self.logger.warning(f"[TRADE] Validation failed: quantity must be positive (got {quantity})")
            raise ValueError("Quantity must be positive")
        if price <= 0:
            self.logger.warning(f"[TRADE] Validation failed: price must be positive (got ${price:.2f})")
            raise ValueError("Price must be positive")
        if quantity > 10000:
            self.logger.warning(f"[TRADE] Validation failed: quantity {quantity} exceeds max (10000)")
            raise ValueError("Order exceeds maximum quantity (10000)")
        
        self.logger.debug(f"[TRADE] Validation passed: symbol={symbol}, quantity={quantity}, price=${price:.2f}")
    
    def _submit_to_exchange(self, trade_id: str, symbol: str, 
                            quantity: int, price: float, side: str):
        """Simulate submitting order to exchange"""
        # Simulate network latency to exchange
        latency = random.uniform(0.1, 0.3)
        time.sleep(latency)
        
        self.logger.debug(f"[TRADE] Exchange submission: {trade_id} | {side} {quantity} {symbol} @ ${price:.2f} | latency: {latency*1000:.0f}ms")
        
        # Simulate occasional exchange errors
        if random.random() < self._failure_rate:
            self.logger.error(f"[TRADE] Exchange connection timeout for order {trade_id} after {latency*1000:.0f}ms")
            raise Exception("Exchange connection timeout")
        
        self._pending_orders[trade_id] = {
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'side': side,
            'submitted_at': datetime.utcnow().isoformat()
        }
        
        self.logger.debug(f"[TRADE] Order {trade_id} added to pending queue | pending_count: {len(self._pending_orders)}")
    
    def _wait_for_fill(self, trade_id: str) -> Dict:
        """Wait for order to be filled"""
        # Simulate waiting for fill
        fill_time = random.uniform(0.05, 0.2)
        time.sleep(fill_time)
        
        self.logger.debug(f"[TRADE] Waiting for fill confirmation: {trade_id} | wait_time: {fill_time*1000:.0f}ms")
        
        # Simulate occasional partial fills or rejections
        if random.random() < self._failure_rate:
            reason = 'Market moved, order rejected'
            self.logger.warning(f"[TRADE] Order {trade_id} NOT filled: {reason}")
            return {'filled': False, 'reason': reason}
        
        self.logger.debug(f"[TRADE] Order {trade_id} FILLED successfully | fill_time: {fill_time*1000:.0f}ms")
        
        if trade_id in self._pending_orders:
            del self._pending_orders[trade_id]
            self.logger.debug(f"[TRADE] Order {trade_id} removed from pending queue | remaining: {len(self._pending_orders)}")
        
        return {'filled': True}
    
    def _process_settlement(self, trade_id: str, user_id: str):
        """Process trade settlement"""
        # Simulate settlement processing
        settle_time = random.uniform(0.02, 0.05)
        time.sleep(settle_time)
        
        self.logger.debug(f"[TRADE] Settlement processed for {trade_id} | user: {user_id} | settle_time: {settle_time*1000:.0f}ms")
    
    def get_trade_history(self, user_id: str) -> List[Dict]:
        """Get user's trade history"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[TRADE] Fetching trade history for user: {user_id}")
            
            trades = self._trades.get(user_id, [])
            
            # Calculate summary stats
            total_value = sum(t.get('total_value', 0) for t in trades)
            buy_count = len([t for t in trades if t.get('side') == 'buy'])
            sell_count = len([t for t in trades if t.get('side') == 'sell'])
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.debug(f"[TRADE] Trade history retrieved: user={user_id} | trades={len(trades)} | buys={buy_count} | sells={sell_count} | total_value=${total_value:.2f} | {duration:.2f}ms")
            self.metrics.record_service_call('TradeService', 'get_trade_history', duration, True)
            
            return trades
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[TRADE] Failed to get trade history for user {user_id}: {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('TradeService', 'get_trade_history', duration, False)
            return []
    
    def get_pending_orders(self, user_id: str) -> List[Dict]:
        """Get user's pending orders"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[TRADE] Fetching pending orders for user: {user_id}")
            
            # Filter pending orders for user (simplified - in reality would be indexed)
            orders = [
                {'trade_id': tid, **order} 
                for tid, order in self._pending_orders.items()
            ]
            
            duration = (time.time() - start_time) * 1000
            self.logger.debug(f"[TRADE] Pending orders retrieved: user={user_id} | count={len(orders)} | {duration:.2f}ms")
            
            return orders
            
        except Exception as e:
            self.logger.error(f"[TRADE] Failed to get pending orders for user {user_id}: {str(e)}")
            return []

