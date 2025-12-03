"""
Authentication Service
======================
Simulates user authentication and session management.

Demonstrates:
- Manual timing of operations
- Logging authentication attempts
- Session token management
"""

import time
import uuid
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
from observability.metrics import Timer


class AuthService:
    """
    Handles user authentication and session management.
    
    In a real system, this would connect to:
    - User database
    - OAuth providers
    - Session store (Redis)
    """
    
    def __init__(self, logger, metrics):
        self.logger = logger
        self.metrics = metrics
        self._sessions: Dict[str, Dict] = {}
        self._users = {
            'demo': {'password': 'demo123', 'name': 'Demo User', 'email': 'demo@tradesim.com'},
            'trader': {'password': 'trade123', 'name': 'Pro Trader', 'email': 'trader@tradesim.com'},
        }
        self._failed_attempts: Dict[str, int] = {}
        
    def health_check(self) -> Dict:
        """Check if auth service is healthy"""
        return {
            'status': 'healthy',
            'active_sessions': len(self._sessions),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def login(self, username: str, password: str) -> Dict:
        """
        Authenticate user and create session.
        
        Manual timing and logging example.
        """
        start_time = time.time()
        
        self.logger.info(f"[AUTH] Login attempt for user: {username}")
        
        # Simulate network latency to auth service
        time.sleep(random.uniform(0.05, 0.15))
        
        # Check if user exists
        user = self._users.get(username.lower())
        
        if not user:
            duration = (time.time() - start_time) * 1000
            self.logger.warning(f"[AUTH] Login failed - user not found: {username} | {duration:.2f}ms")
            self.metrics.record_auth_attempt(False)
            self._record_failed_attempt(username)
            return {'success': False, 'error': 'Invalid credentials'}
        
        # Verify password (in reality, this would be hashed)
        if user['password'] != password:
            duration = (time.time() - start_time) * 1000
            self.logger.warning(f"[AUTH] Login failed - wrong password: {username} | {duration:.2f}ms")
            self.metrics.record_auth_attempt(False)
            self._record_failed_attempt(username)
            return {'success': False, 'error': 'Invalid credentials'}
        
        # Create session token
        token = self._generate_token(username)
        
        # Store session
        self._sessions[token] = {
            'user_id': username,
            'name': user['name'],
            'email': user['email'],
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        duration = (time.time() - start_time) * 1000
        self.logger.info(f"[AUTH] Login successful: {username} | {duration:.2f}ms")
        self.metrics.record_auth_attempt(True)
        self.metrics.record_service_call('AuthService', 'login', duration, True)
        
        return {
            'success': True,
            'token': token,
            'user': {
                'user_id': username,
                'name': user['name'],
                'email': user['email']
            }
        }
    
    def validate_token(self, token: str) -> Dict:
        """Validate a session token"""
        start_time = time.time()
        
        session = self._sessions.get(token)
        
        if not session:
            self.logger.debug(f"[AUTH] Token validation failed - not found")
            return {'valid': False, 'error': 'Invalid or expired token'}
        
        # Check expiration
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.utcnow() > expires_at:
            self.logger.info(f"[AUTH] Token expired for user: {session['user_id']}")
            del self._sessions[token]
            return {'valid': False, 'error': 'Token expired'}
        
        duration = (time.time() - start_time) * 1000
        self.metrics.record_service_call('AuthService', 'validate_token', duration, True)
        
        return {
            'valid': True,
            'user': {
                'user_id': session['user_id'],
                'name': session['name'],
                'email': session['email']
            }
        }
    
    def logout(self, token: str) -> Dict:
        """Invalidate a session"""
        if token in self._sessions:
            user_id = self._sessions[token]['user_id']
            del self._sessions[token]
            self.logger.info(f"[AUTH] Logout successful: {user_id}")
            return {'success': True}
        return {'success': False, 'error': 'Session not found'}
    
    def _generate_token(self, username: str) -> str:
        """Generate a session token"""
        raw = f"{username}{datetime.utcnow().isoformat()}{uuid.uuid4()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    
    def _record_failed_attempt(self, username: str):
        """Track failed login attempts"""
        self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
        
        if self._failed_attempts[username] >= 3:
            self.logger.warning(f"[AUTH] Multiple failed attempts for: {username} (count: {self._failed_attempts[username]})")

