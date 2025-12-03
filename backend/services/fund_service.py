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
import traceback
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
        
        self.logger.info(f"[FUND] FundService initialized | bank_latency_range: {self._bank_api_latency_range[0]*1000:.0f}-{self._bank_api_latency_range[1]*1000:.0f}ms | timeout_rate: {self._bank_timeout_rate*100:.1f}%")
        
    def health_check(self) -> Dict:
        """Check if fund service is healthy"""
        start_time = time.time()
        
        try:
            self.logger.debug("[FUND] Performing health check...")
            
            # Simulate checking connection to bank API
            bank_status = self._check_bank_connection()
            
            status = {
                'status': 'healthy' if bank_status['connected'] else 'degraded',
                'bank_api_status': bank_status,
                'tracked_users': len(self._user_balances),
                'total_tracked_balance': sum(self._user_balances.values()),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            duration = (time.time() - start_time) * 1000
            self.logger.debug(f"[FUND] Health check completed: status={status['status']} | bank_latency={bank_status['latency_ms']}ms | {duration:.2f}ms")
            
            return status
            
        except Exception as e:
            self.logger.error(f"[FUND] Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _check_bank_connection(self) -> Dict:
        """Check connection to bank API"""
        latency = random.uniform(0.02, 0.05)
        time.sleep(latency)
        
        bank_latency = random.randint(50, 150)
        self.logger.debug(f"[FUND] Bank connection check: latency={bank_latency}ms")
        
        return {
            'connected': True,
            'latency_ms': bank_latency
        }
    
    def get_balance(self, user_id: str) -> float:
        """Get user's current balance"""
        balance = self._user_balances.get(user_id, 0.0)
        self.logger.debug(f"[FUND] Balance inquiry: user={user_id} | balance=${balance:.2f}")
        return balance
    
    def set_balance(self, user_id: str, balance: float):
        """Set user's balance (for demo purposes)"""
        try:
            old_balance = self._user_balances.get(user_id, 0.0)
            self._user_balances[user_id] = balance
            self.logger.info(f"[FUND] Balance SET for {user_id}: ${old_balance:.2f} -> ${balance:.2f} | change: ${balance - old_balance:+.2f}")
        except Exception as e:
            self.logger.error(f"[FUND] Failed to set balance for {user_id}: {str(e)}")
            raise
    
    def add_balance(self, user_id: str, amount: float):
        """Add to user's balance"""
        try:
            current = self._user_balances.get(user_id, 0.0)
            new_balance = current + amount
            self._user_balances[user_id] = new_balance
            self.logger.info(f"[FUND] Balance ADDED for {user_id}: ${current:.2f} + ${amount:.2f} = ${new_balance:.2f}")
        except Exception as e:
            self.logger.error(f"[FUND] Failed to add balance for {user_id}: {str(e)}")
            raise
    
    def deduct_balance(self, user_id: str, amount: float) -> bool:
        """Deduct from user's balance"""
        try:
            current = self._user_balances.get(user_id, 0.0)
            
            if current < amount:
                self.logger.warning(f"[FUND] Balance DEDUCTION FAILED for {user_id}: insufficient funds | current=${current:.2f} | requested=${amount:.2f} | shortfall=${amount - current:.2f}")
                return False
            
            new_balance = current - amount
            self._user_balances[user_id] = new_balance
            self.logger.info(f"[FUND] Balance DEDUCTED for {user_id}: ${current:.2f} - ${amount:.2f} = ${new_balance:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"[FUND] Failed to deduct balance for {user_id}: {str(e)}")
            return False
    
    def verify_funds(self, user_id: str, amount: float) -> Dict:
        """
        Verify user has sufficient funds.
        
        This simulates calling an external bank API.
        """
        start_time = time.time()
        
        self.logger.info(f"[FUND] ===== FUND VERIFICATION START =====")
        self.logger.info(f"[FUND] Verifying funds for user: {user_id} | required: ${amount:.2f}")
        
        bank_api_success = True
        
        # Simulate bank API call
        try:
            self.logger.debug(f"[FUND] Calling bank API to verify balance for {user_id}...")
            api_start = time.time()
            self._call_bank_api('verify_balance')
            api_duration = (time.time() - api_start) * 1000
            self.logger.debug(f"[FUND] Bank API verify_balance succeeded | {api_duration:.2f}ms")
        except Exception as e:
            bank_api_success = False
            self.logger.error(f"[FUND] Bank API error during verification: {str(e)}")
            self.logger.warning(f"[FUND] Falling back to cached balance for {user_id} (degraded mode)")
        
        available = self._user_balances.get(user_id, 0.0)
        sufficient = available >= amount
        shortfall = amount - available if not sufficient else 0
        
        duration = (time.time() - start_time) * 1000
        
        if sufficient:
            self.logger.info(f"[FUND] ✓ FUNDS SUFFICIENT: user={user_id} | available=${available:.2f} | required=${amount:.2f} | surplus=${available - amount:.2f}")
        else:
            self.logger.warning(f"[FUND] ✗ FUNDS INSUFFICIENT: user={user_id} | available=${available:.2f} | required=${amount:.2f} | shortfall=${shortfall:.2f}")
        
        self.logger.info(f"[FUND] Verification complete | bank_api_ok={bank_api_success} | {duration:.2f}ms")
        self.logger.info(f"[FUND] ===== FUND VERIFICATION END =====")
        
        self.metrics.record_service_call('FundService', 'verify_funds', duration, True)
        
        return {
            'sufficient': sufficient,
            'available': available,
            'required': amount,
            'shortfall': shortfall if not sufficient else 0
        }
    
    def authenticate_transfer(self, user_id: str, amount: float, 
                              transfer_type: str) -> Dict:
        """
        Authenticate a bank transfer.
        
        This simulates multi-factor authentication with the bank.
        """
        start_time = time.time()
        
        self.logger.info(f"[FUND] ===== TRANSFER AUTHENTICATION START =====")
        self.logger.info(f"[FUND] Authenticating {transfer_type.upper()} transfer | user={user_id} | amount=${amount:.2f}")
        
        # Step 1: Initial authentication
        try:
            self.logger.debug(f"[FUND] Step 1/3: Bank authentication for {user_id}...")
            auth_start = time.time()
            self._call_bank_api('authenticate')
            auth_time = (time.time() - auth_start) * 1000
            self.logger.debug(f"[FUND] Step 1/3: Bank authentication successful | {auth_time:.2f}ms")
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[FUND] Step 1/3: Bank authentication FAILED: {str(e)}")
            self.logger.error(f"[FUND] Transfer authentication aborted | {duration:.2f}ms")
            self.logger.info(f"[FUND] ===== TRANSFER AUTHENTICATION END (FAILED) =====")
            self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, False)
            return {'authenticated': False, 'error': 'Bank authentication timeout'}
        
        # Step 2: Verify transfer authorization
        try:
            self.logger.debug(f"[FUND] Step 2/3: Transfer authorization for {user_id} | amount=${amount:.2f}...")
            authz_start = time.time()
            self._call_bank_api('authorize_transfer')
            authz_time = (time.time() - authz_start) * 1000
            self.logger.debug(f"[FUND] Step 2/3: Transfer authorization successful | {authz_time:.2f}ms")
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[FUND] Step 2/3: Transfer authorization FAILED: {str(e)}")
            self.logger.error(f"[FUND] Transfer authentication aborted | {duration:.2f}ms")
            self.logger.info(f"[FUND] ===== TRANSFER AUTHENTICATION END (FAILED) =====")
            self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, False)
            return {'authenticated': False, 'error': 'Transfer authorization failed'}
        
        # Step 3: Fraud check
        self.logger.debug(f"[FUND] Step 3/3: Fraud check for {user_id} | {transfer_type} ${amount:.2f}...")
        fraud_start = time.time()
        fraud_result = self._check_fraud(user_id, amount, transfer_type)
        fraud_time = (time.time() - fraud_start) * 1000
        
        if fraud_result['flagged']:
            duration = (time.time() - start_time) * 1000
            self.logger.warning(f"[FUND] Step 3/3: Fraud check FLAGGED transaction!")
            self.logger.warning(f"[FUND] Suspicious activity detected: user={user_id} | type={transfer_type} | amount=${amount:.2f}")
            self.logger.info(f"[FUND] ===== TRANSFER AUTHENTICATION END (FLAGGED) =====")
            self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, False)
            return {'authenticated': False, 'error': 'Transaction flagged for review'}
        
        self.logger.debug(f"[FUND] Step 3/3: Fraud check passed | {fraud_time:.2f}ms")
        
        duration = (time.time() - start_time) * 1000
        auth_code = f"AUTH-{user_id[:4].upper()}-{int(time.time())}"
        
        self.logger.info(f"[FUND] ✓ TRANSFER AUTHENTICATED: user={user_id} | type={transfer_type} | amount=${amount:.2f}")
        self.logger.info(f"[FUND] Authorization code: {auth_code}")
        self.logger.info(f"[FUND] Total auth time: {duration:.2f}ms")
        self.logger.info(f"[FUND] ===== TRANSFER AUTHENTICATION END (SUCCESS) =====")
        
        self.metrics.record_service_call('FundService', 'authenticate_transfer', duration, True)
        
        return {
            'authenticated': True,
            'authorization_code': auth_code
        }
    
    def _call_bank_api(self, operation: str):
        """Simulate calling external bank API"""
        # Simulate network latency
        latency = random.uniform(*self._bank_api_latency_range)
        time.sleep(latency)
        
        self.logger.debug(f"[FUND] Bank API call: operation={operation} | simulated_latency={latency*1000:.0f}ms")
        
        # Simulate occasional timeouts
        if random.random() < self._bank_timeout_rate:
            self.logger.error(f"[FUND] Bank API TIMEOUT: operation={operation} | after {latency*1000:.0f}ms")
            raise TimeoutError(f"Bank API timeout for {operation}")
        
        self.logger.debug(f"[FUND] Bank API call successful: operation={operation}")
    
    def _check_fraud(self, user_id: str, amount: float, transfer_type: str) -> Dict:
        """Simulate fraud detection"""
        check_time = random.uniform(0.02, 0.05)
        time.sleep(check_time)
        
        self.logger.debug(f"[FRAUD] Running fraud check: user={user_id} | type={transfer_type} | amount=${amount:.2f}")
        
        # Flag unusually large transactions
        flagged = amount > 1000000  # Flag transactions over $1M
        
        # Additional logging for fraud analysis
        risk_factors = []
        if amount > 100000:
            risk_factors.append(f"large_amount (${amount:.2f})")
        if amount > 500000:
            risk_factors.append("very_large_amount")
        if amount > 1000000:
            risk_factors.append("exceeds_threshold")
        
        if risk_factors:
            self.logger.debug(f"[FRAUD] Risk factors detected: {', '.join(risk_factors)}")
        
        if flagged:
            self.logger.warning(f"[FRAUD] ⚠ TRANSACTION FLAGGED: user={user_id} | amount=${amount:.2f} | factors={risk_factors}")
        else:
            self.logger.debug(f"[FRAUD] Check passed: user={user_id} | amount=${amount:.2f} | check_time={check_time*1000:.0f}ms")
        
        return {
            'flagged': flagged,
            'risk_factors': risk_factors,
            'check_duration_ms': round(check_time * 1000, 2)
        }

