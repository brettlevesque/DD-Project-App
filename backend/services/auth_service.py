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
import traceback
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
        self.logger.info("[AUTH] AuthService initialized with {} registered users".format(len(self._users)))
        
    def health_check(self) -> Dict:
        """Check if auth service is healthy"""
        try:
            status = {
                'status': 'healthy',
                'active_sessions': len(self._sessions),
                'failed_attempts_tracked': len(self._failed_attempts),
                'timestamp': datetime.utcnow().isoformat()
            }
            self.logger.debug(f"[AUTH] Health check completed: {status['active_sessions']} active sessions")
            return status
        except Exception as e:
            self.logger.error(f"[AUTH] Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def login(self, username: str, password: str) -> Dict:
        """
        Authenticate user and create session.
        
        Manual timing and logging example.
        """
        start_time = time.time()
        
        self.logger.info(f"[AUTH] Login attempt initiated for user: {username}")
        self.logger.debug(f"[AUTH] Checking credentials for user: {username} | password length: {len(password) if password else 0}")
        
        try:
            # Check for locked accounts due to too many failed attempts
            if self._failed_attempts.get(username, 0) >= 5:
                duration = (time.time() - start_time) * 1000
                self.logger.warning(f"[AUTH] Login blocked - account locked due to too many failed attempts: {username} | attempts: {self._failed_attempts[username]} | {duration:.2f}ms")
                self.metrics.record_auth_attempt(False)
                return {'success': False, 'error': 'Account temporarily locked. Please try again later.'}
            
            # Simulate network latency to auth service
            latency = random.uniform(0.05, 0.15)
            time.sleep(latency)
            self.logger.debug(f"[AUTH] Simulated auth service latency: {latency*1000:.2f}ms")
            
            # Check if user exists
            user = self._users.get(username.lower())
            
            if not user:
                duration = (time.time() - start_time) * 1000
                self.logger.warning(f"[AUTH] Login failed - user not found in database: {username} | total_users: {len(self._users)} | {duration:.2f}ms")
                self.metrics.record_auth_attempt(False)
                self._record_failed_attempt(username)
                return {'success': False, 'error': 'Invalid credentials'}
            
            self.logger.debug(f"[AUTH] User found: {username} | name: {user['name']} | email: {user['email']}")
            
            # Verify password (in reality, this would be hashed)
            if user['password'] != password:
                duration = (time.time() - start_time) * 1000
                failed_count = self._failed_attempts.get(username, 0) + 1
                self.logger.warning(f"[AUTH] Login failed - wrong password: {username} | failed_attempts: {failed_count} | {duration:.2f}ms")
                self.metrics.record_auth_attempt(False)
                self._record_failed_attempt(username)
                return {'success': False, 'error': 'Invalid credentials'}
            
            self.logger.debug(f"[AUTH] Password verified successfully for user: {username}")
            
            # Create session token
            token = self._generate_token(username)
            self.logger.debug(f"[AUTH] Session token generated for user: {username} | token_prefix: {token[:8]}...")
            
            # Store session
            session_data = {
                'user_id': username,
                'name': user['name'],
                'email': user['email'],
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
            self._sessions[token] = session_data
            
            # Clear failed attempts on successful login
            if username in self._failed_attempts:
                self.logger.debug(f"[AUTH] Clearing {self._failed_attempts[username]} failed attempts for user: {username}")
                del self._failed_attempts[username]
            
            duration = (time.time() - start_time) * 1000
            self.logger.info(f"[AUTH] Login successful: {username} | session_expires: {session_data['expires_at']} | active_sessions: {len(self._sessions)} | {duration:.2f}ms")
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
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[AUTH] Login error for user {username}: {str(e)} | {duration:.2f}ms")
            self.logger.error(f"[AUTH] Traceback: {traceback.format_exc()}")
            self.metrics.record_auth_attempt(False)
            self.metrics.record_service_call('AuthService', 'login', duration, False)
            return {'success': False, 'error': 'An internal error occurred during authentication'}
    
    def validate_token(self, token: str) -> Dict:
        """Validate a session token"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[AUTH] Validating token: {token[:8] if token else 'None'}...")
            
            if not token:
                self.logger.warning("[AUTH] Token validation failed - empty token provided")
                return {'valid': False, 'error': 'No token provided'}
            
            session = self._sessions.get(token)
            
            if not session:
                self.logger.warning(f"[AUTH] Token validation failed - token not found in {len(self._sessions)} active sessions | token_prefix: {token[:8]}...")
                return {'valid': False, 'error': 'Invalid or expired token'}
            
            self.logger.debug(f"[AUTH] Token found for user: {session['user_id']} | created: {session['created_at']}")
            
            # Check expiration
            expires_at = datetime.fromisoformat(session['expires_at'])
            time_remaining = (expires_at - datetime.utcnow()).total_seconds()
            
            if datetime.utcnow() > expires_at:
                self.logger.info(f"[AUTH] Token expired for user: {session['user_id']} | expired_at: {session['expires_at']}")
                del self._sessions[token]
                return {'valid': False, 'error': 'Token expired'}
            
            duration = (time.time() - start_time) * 1000
            self.logger.debug(f"[AUTH] Token validated successfully for user: {session['user_id']} | time_remaining: {time_remaining:.0f}s | {duration:.2f}ms")
            self.metrics.record_service_call('AuthService', 'validate_token', duration, True)
            
            return {
                'valid': True,
                'user': {
                    'user_id': session['user_id'],
                    'name': session['name'],
                    'email': session['email']
                }
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[AUTH] Token validation error: {str(e)} | {duration:.2f}ms")
            self.logger.error(f"[AUTH] Traceback: {traceback.format_exc()}")
            self.metrics.record_service_call('AuthService', 'validate_token', duration, False)
            return {'valid': False, 'error': 'An internal error occurred during token validation'}
    
    def logout(self, token: str) -> Dict:
        """Invalidate a session"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[AUTH] Logout requested for token: {token[:8] if token else 'None'}...")
            
            if token in self._sessions:
                user_id = self._sessions[token]['user_id']
                session_created = self._sessions[token]['created_at']
                del self._sessions[token]
                duration = (time.time() - start_time) * 1000
                self.logger.info(f"[AUTH] Logout successful: {user_id} | session_created: {session_created} | remaining_sessions: {len(self._sessions)} | {duration:.2f}ms")
                self.metrics.record_service_call('AuthService', 'logout', duration, True)
                return {'success': True}
            
            duration = (time.time() - start_time) * 1000
            self.logger.warning(f"[AUTH] Logout failed - session not found | token_prefix: {token[:8] if token else 'None'}... | {duration:.2f}ms")
            self.metrics.record_service_call('AuthService', 'logout', duration, False)
            return {'success': False, 'error': 'Session not found'}
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[AUTH] Logout error: {str(e)} | {duration:.2f}ms")
            self.logger.error(f"[AUTH] Traceback: {traceback.format_exc()}")
            self.metrics.record_service_call('AuthService', 'logout', duration, False)
            return {'success': False, 'error': 'An internal error occurred during logout'}
    
    def _generate_token(self, username: str) -> str:
        """Generate a session token"""
        raw = f"{username}{datetime.utcnow().isoformat()}{uuid.uuid4()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    
    def _record_failed_attempt(self, username: str):
        """Track failed login attempts"""
        self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
        
        if self._failed_attempts[username] >= 3:
            self.logger.warning(f"[AUTH] Multiple failed attempts for: {username} (count: {self._failed_attempts[username]})")

