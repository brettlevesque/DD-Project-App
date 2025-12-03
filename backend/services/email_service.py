"""
Email Notification Service
==========================
Simulates sending email notifications for trades and alerts.

Demonstrates:
- Async operation simulation
- Queue management
- Delivery tracking
"""

import time
import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from threading import Thread


class EmailService:
    """
    Handles email notifications for the trading platform.
    
    In a real system, this would:
    - Queue emails for async processing
    - Connect to SMTP/SendGrid/SES
    - Track delivery status
    - Handle bounces and complaints
    """
    
    def __init__(self, logger, metrics):
        self.logger = logger
        self.metrics = metrics
        self._email_queue: List[Dict] = []
        self._sent_emails: List[Dict] = []
        
        # Simulate email service behavior
        self._smtp_latency_range = (0.1, 0.3)  # 100-300ms
        self._delivery_failure_rate = 0.02  # 2% failure rate
        
    def health_check(self) -> Dict:
        """Check if email service is healthy"""
        return {
            'status': 'healthy',
            'queue_size': len(self._email_queue),
            'sent_last_hour': len([e for e in self._sent_emails 
                                  if self._is_recent(e.get('sent_at'))]),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _is_recent(self, timestamp_str: Optional[str]) -> bool:
        """Check if timestamp is within last hour"""
        if not timestamp_str:
            return False
        try:
            ts = datetime.fromisoformat(timestamp_str)
            return (datetime.utcnow() - ts).total_seconds() < 3600
        except:
            return False
    
    def send_trade_confirmation(self, user_id: str, trade: Dict) -> Dict:
        """
        Send trade confirmation email.
        
        This simulates:
        1. Building email template
        2. Queuing for delivery
        3. SMTP submission
        4. Delivery tracking
        """
        start_time = time.time()
        email_id = str(uuid.uuid4())[:8]
        
        self.logger.info(f"[EMAIL] Sending trade confirmation: {email_id} | user: {user_id} | trade: {trade['trade_id']}")
        
        # Build email content
        email = {
            'email_id': email_id,
            'type': 'trade_confirmation',
            'to': f"{user_id}@example.com",  # Simulated
            'subject': f"Trade Confirmation - {trade['side'].upper()} {trade['symbol']}",
            'body': self._build_trade_email_body(trade),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        # Simulate SMTP delivery
        try:
            self._send_via_smtp(email)
            email['status'] = 'sent'
            email['sent_at'] = datetime.utcnow().isoformat()
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.info(f"[EMAIL] Sent: {email_id} | to: {email['to']} | {duration:.2f}ms")
            self.metrics.record_email_sent()
            self.metrics.record_service_call('EmailService', 'send_trade_confirmation', duration, True)
            
            self._sent_emails.append(email)
            
            return {'success': True, 'email_id': email_id}
            
        except Exception as e:
            email['status'] = 'failed'
            email['error'] = str(e)
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.error(f"[EMAIL] Failed: {email_id} | error: {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('EmailService', 'send_trade_confirmation', duration, False)
            
            # Queue for retry
            self._email_queue.append(email)
            
            return {'success': False, 'error': str(e), 'email_id': email_id}
    
    def send_alert(self, user_id: str, alert_type: str, message: str) -> Dict:
        """Send alert email to user"""
        start_time = time.time()
        email_id = str(uuid.uuid4())[:8]
        
        self.logger.info(f"[EMAIL] Sending alert: {email_id} | user: {user_id} | type: {alert_type}")
        
        email = {
            'email_id': email_id,
            'type': 'alert',
            'to': f"{user_id}@example.com",
            'subject': f"TradeSim Alert: {alert_type}",
            'body': message,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        try:
            self._send_via_smtp(email)
            email['status'] = 'sent'
            email['sent_at'] = datetime.utcnow().isoformat()
            
            duration = (time.time() - start_time) * 1000
            self.metrics.record_email_sent()
            self.metrics.record_service_call('EmailService', 'send_alert', duration, True)
            
            self._sent_emails.append(email)
            
            return {'success': True, 'email_id': email_id}
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[EMAIL] Alert failed: {email_id} | error: {str(e)}")
            self.metrics.record_service_call('EmailService', 'send_alert', duration, False)
            
            return {'success': False, 'error': str(e), 'email_id': email_id}
    
    def send_daily_summary(self, user_id: str, portfolio_value: float, 
                          daily_change: float, trades_today: int) -> Dict:
        """Send daily portfolio summary"""
        start_time = time.time()
        email_id = str(uuid.uuid4())[:8]
        
        change_str = f"+${daily_change:.2f}" if daily_change >= 0 else f"-${abs(daily_change):.2f}"
        
        email = {
            'email_id': email_id,
            'type': 'daily_summary',
            'to': f"{user_id}@example.com",
            'subject': f"Daily Summary - Portfolio: ${portfolio_value:.2f} ({change_str})",
            'body': f"""
Daily Portfolio Summary
=======================
Portfolio Value: ${portfolio_value:.2f}
Today's Change: {change_str}
Trades Today: {trades_today}
            """,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            self._send_via_smtp(email)
            duration = (time.time() - start_time) * 1000
            self.metrics.record_email_sent()
            self._sent_emails.append(email)
            
            return {'success': True, 'email_id': email_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _build_trade_email_body(self, trade: Dict) -> str:
        """Build trade confirmation email body"""
        return f"""
Trade Confirmation
==================

Trade ID: {trade['trade_id']}
Type: {trade['side'].upper()}
Symbol: {trade['symbol']}
Quantity: {trade['quantity']}
Price: ${trade['price']:.2f}
Total Value: ${trade['total_value']:.2f}
Fees: ${trade.get('fees', 0):.2f}

Executed at: {trade['executed_at']}
Status: {trade['status']}

Thank you for trading with TradeSim!
        """
    
    def _send_via_smtp(self, email: Dict):
        """Simulate sending email via SMTP"""
        # Simulate SMTP latency
        latency = random.uniform(*self._smtp_latency_range)
        time.sleep(latency)
        
        self.logger.debug(f"[EMAIL] SMTP connection | latency: {latency*1000:.0f}ms")
        
        # Simulate occasional delivery failures
        if random.random() < self._delivery_failure_rate:
            raise Exception("SMTP connection refused")
    
    def get_queue_status(self) -> Dict:
        """Get email queue status"""
        return {
            'pending': len(self._email_queue),
            'sent_total': len(self._sent_emails),
            'failed': len([e for e in self._sent_emails if e.get('status') == 'failed'])
        }
    
    def process_queue(self) -> int:
        """Process pending emails in queue"""
        processed = 0
        failed = []
        
        for email in self._email_queue:
            try:
                self._send_via_smtp(email)
                email['status'] = 'sent'
                email['sent_at'] = datetime.utcnow().isoformat()
                self._sent_emails.append(email)
                processed += 1
            except Exception as e:
                email['retry_count'] = email.get('retry_count', 0) + 1
                if email['retry_count'] < 3:
                    failed.append(email)
                else:
                    email['status'] = 'permanently_failed'
                    self._sent_emails.append(email)
        
        self._email_queue = failed
        
        self.logger.info(f"[EMAIL] Queue processed: {processed} sent, {len(failed)} pending retry")
        
        return processed

