"""
Fund Verification & Bank Transfer Service
==========================================
Simulates fund verification and bank transfer authentication.

Demonstrates:
- External service calls (to "bank API")
- Timeout handling
- Retry logic
"""

import time
import random
from datetime import datetime
from typing import Dict


class FundService:
    """
    Handles fund verification and bank transfer authentication.
    
    In a real system, this would:
    - Connect to banking APIs
    - Verify account balances
    - Process ACH/wire transfers
    - Handle fraud detection
    """
    
    def __init__(self, logger, metrics):
        self.logger = logger
        self.metrics = metrics
        self._user_balances: Dict[str, float] = {}
        
        # Simulate external bank API behavior
        self._bank_api_latency_range = (0.1, 0.4)  # 100-400ms latency
        self._bank_timeout_rate = 0.03  # 3% timeout rate
        
    def health_check(self) -> Dict:
        """Check if fund service is healthy"""
        # Simulate checking connection to bank API
        bank_status = self._check_bank_connection()
        
        return {
            'status': 'healthy' if bank_status['connected'] else 'degraded',
            'bank_api_status': bank_status,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _check_bank_connection(self) -> Dict:
        """Check connection to bank API"""
        time.sleep(random.uniform(0.02, 0.05))
        return {
            'connected': True,
            'latency_ms': random.randint(50, 150)
        }
    
    def get_balance(self, user_id: str) -> float:
        """Get user's current balance"""
        return self._user_balances.get(user_id, 0.0)
    
    def set_balance(self, user_id: str, balance: float):
        """Set user's balance (for demo purposes)"""
        self._user_balances[user_id] = balance
        self.logger.info(f"[FUND] Balance set for {user_id}: ${balance:.2f}")
    
    def add_balance(self, user_id: str, amount: float):
        """Add to user's balance"""
        current = self._user_balances.get(user_id, 0.0)
        self._user_balances[user_id] = current + amount
        self.logger.debug(f"[FUND] Balance updated for {user_id}: ${current:.2f} -> ${self._user_balances[user_id]:.2f}")
    
    def deduct_balance(self, user_id: str, amount: float) -> bool:
        """Deduct from user's balance"""
        current = self._user_balances.get(user_id, 0.0)
        if current < amount:
            return False
        self._user_balances[user_id] = current - amount
        self.logger.debug(f"[FUND] Balance deducted for {user_id}: ${current:.2f} -> ${self._user_balances[user_id]:.2f}")
        return True
    
    def verify_funds(self, user_id: str, amount: float) -> Dict:
        """
        Verify user has sufficient funds.
        
        This simulates calling an external bank API.
        """
        start_time = time.time()
        
        self.logger.info(f"[FUND] Verifying funds for {user_id}: ${amount:.2f}")
        
        # Simulate bank API call
        try:
            self._call_bank_api('verify_balance')
        except Exception as e:
            self.logger.error(f"[FUND] Bank API error during verification: {str(e)}")
            # In degraded mode, use cached balance
            self.logger.warning(f"[FUND] Using cached balance for {user_id}")
        
        available = self._user_balances.get(user_id, 0.0)
        sufficient = available >= amount
        
        duration = (time.time() - start_time) * 1000
        
        self.logger.info(
            f"[FUND] Verification complete for {user_id}: "
            f"needed=${amount:.2f}, available=${available:.2f}, sufficient={sufficient} | {duration:.2f}ms"
        )
        
        self.metrics.record_service_call('FundService', 'verify_funds', duration, True)
        
        return {
            'sufficient': sufficient,
            'available': available,
            'required': amount
        }
    
    def authenticate_transfer(self, user_id: str, amount: float, 
                              transfer_type: str) -> Dict:
        """
        Authenticate a bank transfer.
        
        This simulates multi-factor authentication with the bank.
        """
        start_time = time.time()
        
        self.logger.info(f"[FUND] Authenticating {transfer_type} transfer for {user_id}: ${amount:.2f}")
        
        # Step 1: Initial authentication
        try:
            self._call_bank_api('authenticate')
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[FUND] Bank authentication failed: {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, False)
            return {'authenticated': False, 'error': 'Bank authentication timeout'}
        
        # Step 2: Verify transfer authorization
        try:
            self._call_bank_api('authorize_transfer')
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[FUND] Transfer authorization failed: {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, False)
            return {'authenticated': False, 'error': 'Transfer authorization failed'}
        
        # Step 3: Fraud check
        fraud_result = self._check_fraud(user_id, amount, transfer_type)
        if fraud_result['flagged']:
            duration = (time.time() - start_time) * 1000
            self.logger.warning(f"[FUND] Fraud check flagged transfer for {user_id} | {duration:.2f}ms")
            self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, False)
            return {'authenticated': False, 'error': 'Transaction flagged for review'}
        
        duration = (time.time() - start_time) * 1000
        
        self.logger.info(f"[FUND] Transfer authenticated for {user_id}: ${amount:.2f} | {duration:.2f}ms")
        self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, True)
        
        return {
            'authenticated': True,
            'authorization_code': f"AUTH-{user_id[:4].upper()}-{int(time.time())}"
        }
    
    def _call_bank_api(self, operation: str):
        """Simulate calling external bank API"""
        # Simulate network latency
        latency = random.uniform(*self._bank_api_latency_range)
        time.sleep(latency)
        
        self.logger.debug(f"[FUND] Bank API call: {operation} | latency: {latency*1000:.0f}ms")
        
        # Simulate occasional timeouts
        if random.random() < self._bank_timeout_rate:
            raise TimeoutError(f"Bank API timeout for {operation}")
    
    def _check_fraud(self, user_id: str, amount: float, transfer_type: str) -> Dict:
        """Simulate fraud detection"""
        time.sleep(random.uniform(0.02, 0.05))
        
        # Flag unusually large transactions
        flagged = amount > 1000000  # Flag transactions over $1M
        
        if flagged:
            self.logger.warning(f"[FRAUD] Large transaction flagged: {user_id} ${amount:.2f}")
        
        return {'flagged': flagged}

