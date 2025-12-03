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
import traceback
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
        
        self.logger.info(f"[EMAIL] EmailService initialized | smtp_latency: {self._smtp_latency_range[0]*1000:.0f}-{self._smtp_latency_range[1]*1000:.0f}ms | failure_rate: {self._delivery_failure_rate*100:.1f}%")
        
    def health_check(self) -> Dict:
        """Check if email service is healthy"""
        try:
            sent_last_hour = len([e for e in self._sent_emails if self._is_recent(e.get('sent_at'))])
            failed_count = len([e for e in self._sent_emails if e.get('status') == 'failed'])
            
            status = {
                'status': 'healthy',
                'queue_size': len(self._email_queue),
                'sent_last_hour': sent_last_hour,
                'total_sent': len(self._sent_emails),
                'failed_count': failed_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.debug(f"[EMAIL] Health check: queue={len(self._email_queue)} | sent_last_hour={sent_last_hour} | total={len(self._sent_emails)}")
            return status
            
        except Exception as e:
            self.logger.error(f"[EMAIL] Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
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
        
        self.logger.info(f"[EMAIL] ===== TRADE CONFIRMATION EMAIL START =====")
        self.logger.info(f"[EMAIL] Preparing trade confirmation: email_id={email_id}")
        self.logger.info(f"[EMAIL] Trade details: user={user_id} | trade_id={trade['trade_id']} | {trade['side'].upper()} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
        
        # Build email content
        recipient = f"{user_id}@example.com"
        subject = f"Trade Confirmation - {trade['side'].upper()} {trade['symbol']}"
        
        email = {
            'email_id': email_id,
            'type': 'trade_confirmation',
            'to': recipient,
            'subject': subject,
            'body': self._build_trade_email_body(trade),
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending',
            'trade_id': trade['trade_id']
        }
        
        self.logger.debug(f"[EMAIL] Email built: to={recipient} | subject={subject}")
        
        # Simulate SMTP delivery
        try:
            self.logger.debug(f"[EMAIL] Connecting to SMTP server...")
            self._send_via_smtp(email)
            
            email['status'] = 'sent'
            email['sent_at'] = datetime.utcnow().isoformat()
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.info(f"[EMAIL] ✓ SENT: {email_id} | to: {recipient} | trade: {trade['trade_id']}")
            self.logger.info(f"[EMAIL] Delivery time: {duration:.2f}ms | total_sent: {len(self._sent_emails) + 1}")
            self.logger.info(f"[EMAIL] ===== TRADE CONFIRMATION EMAIL END (SUCCESS) =====")
            
            self.metrics.record_email_sent()
            self.metrics.record_service_call('EmailService', 'send_trade_confirmation', duration, True)
            
            self._sent_emails.append(email)
            
            return {'success': True, 'email_id': email_id}
            
        except Exception as e:
            email['status'] = 'failed'
            email['error'] = str(e)
            email['retry_count'] = 0
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.error(f"[EMAIL] ✗ FAILED: {email_id} | error: {str(e)}")
            self.logger.error(f"[EMAIL] Queuing for retry | current_queue: {len(self._email_queue) + 1}")
            self.logger.info(f"[EMAIL] ===== TRADE CONFIRMATION EMAIL END (FAILED) =====")
            
            self.metrics.record_service_call('EmailService', 'send_trade_confirmation', duration, False)
            
            # Queue for retry
            self._email_queue.append(email)
            
            return {'success': False, 'error': str(e), 'email_id': email_id}
    
    def send_alert(self, user_id: str, alert_type: str, message: str) -> Dict:
        """Send alert email to user"""
        start_time = time.time()
        email_id = str(uuid.uuid4())[:8]
        
        self.logger.info(f"[EMAIL] ===== ALERT EMAIL START =====")
        self.logger.info(f"[EMAIL] Sending alert: email_id={email_id} | user={user_id} | type={alert_type}")
        self.logger.debug(f"[EMAIL] Alert message: {message[:100]}..." if len(message) > 100 else f"[EMAIL] Alert message: {message}")
        
        recipient = f"{user_id}@example.com"
        
        email = {
            'email_id': email_id,
            'type': 'alert',
            'alert_type': alert_type,
            'to': recipient,
            'subject': f"TradeSim Alert: {alert_type}",
            'body': message,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        try:
            self.logger.debug(f"[EMAIL] Connecting to SMTP for alert delivery...")
            self._send_via_smtp(email)
            email['status'] = 'sent'
            email['sent_at'] = datetime.utcnow().isoformat()
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.info(f"[EMAIL] ✓ ALERT SENT: {email_id} | to: {recipient} | type: {alert_type} | {duration:.2f}ms")
            self.logger.info(f"[EMAIL] ===== ALERT EMAIL END (SUCCESS) =====")
            
            self.metrics.record_email_sent()
            self.metrics.record_service_call('EmailService', 'send_alert', duration, True)
            
            self._sent_emails.append(email)
            
            return {'success': True, 'email_id': email_id}
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[EMAIL] ✗ ALERT FAILED: {email_id} | error: {str(e)} | {duration:.2f}ms")
            self.logger.info(f"[EMAIL] ===== ALERT EMAIL END (FAILED) =====")
            
            self.metrics.record_service_call('EmailService', 'send_alert', duration, False)
            
            return {'success': False, 'error': str(e), 'email_id': email_id}
    
    def send_daily_summary(self, user_id: str, portfolio_value: float, 
                          daily_change: float, trades_today: int) -> Dict:
        """Send daily portfolio summary"""
        start_time = time.time()
        email_id = str(uuid.uuid4())[:8]
        
        change_str = f"+${daily_change:.2f}" if daily_change >= 0 else f"-${abs(daily_change):.2f}"
        change_pct = (daily_change / (portfolio_value - daily_change) * 100) if (portfolio_value - daily_change) > 0 else 0
        
        self.logger.info(f"[EMAIL] ===== DAILY SUMMARY EMAIL START =====")
        self.logger.info(f"[EMAIL] Sending daily summary: email_id={email_id} | user={user_id}")
        self.logger.info(f"[EMAIL] Portfolio: ${portfolio_value:.2f} | change: {change_str} ({change_pct:+.2f}%) | trades: {trades_today}")
        
        recipient = f"{user_id}@example.com"
        
        email = {
            'email_id': email_id,
            'type': 'daily_summary',
            'to': recipient,
            'subject': f"Daily Summary - Portfolio: ${portfolio_value:.2f} ({change_str})",
            'body': f"""
Daily Portfolio Summary
=======================
Portfolio Value: ${portfolio_value:.2f}
Today's Change: {change_str} ({change_pct:+.2f}%)
Trades Today: {trades_today}
            """,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        try:
            self.logger.debug(f"[EMAIL] Connecting to SMTP for daily summary...")
            self._send_via_smtp(email)
            
            email['status'] = 'sent'
            email['sent_at'] = datetime.utcnow().isoformat()
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.info(f"[EMAIL] ✓ DAILY SUMMARY SENT: {email_id} | to: {recipient} | {duration:.2f}ms")
            self.logger.info(f"[EMAIL] ===== DAILY SUMMARY EMAIL END (SUCCESS) =====")
            
            self.metrics.record_email_sent()
            self._sent_emails.append(email)
            
            return {'success': True, 'email_id': email_id}
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[EMAIL] ✗ DAILY SUMMARY FAILED: {email_id} | error: {str(e)} | {duration:.2f}ms")
            self.logger.info(f"[EMAIL] ===== DAILY SUMMARY EMAIL END (FAILED) =====")
            
            return {'success': False, 'error': str(e), 'email_id': email_id}
    
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
        
        self.logger.debug(f"[EMAIL] SMTP connection established | latency: {latency*1000:.0f}ms | recipient: {email.get('to', 'unknown')}")
        
        # Simulate occasional delivery failures
        if random.random() < self._delivery_failure_rate:
            self.logger.error(f"[EMAIL] SMTP connection REFUSED for email: {email.get('email_id', 'unknown')}")
            raise Exception("SMTP connection refused")
        
        self.logger.debug(f"[EMAIL] SMTP delivery successful for email: {email.get('email_id', 'unknown')}")
    
    def get_queue_status(self) -> Dict:
        """Get email queue status"""
        pending = len(self._email_queue)
        sent = len(self._sent_emails)
        failed = len([e for e in self._sent_emails if e.get('status') == 'failed'])
        permanently_failed = len([e for e in self._sent_emails if e.get('status') == 'permanently_failed'])
        
        self.logger.debug(f"[EMAIL] Queue status: pending={pending} | sent={sent} | failed={failed} | permanently_failed={permanently_failed}")
        
        return {
            'pending': pending,
            'sent_total': sent,
            'failed': failed,
            'permanently_failed': permanently_failed
        }
    
    def process_queue(self) -> int:
        """Process pending emails in queue"""
        start_time = time.time()
        
        if not self._email_queue:
            self.logger.debug("[EMAIL] Queue is empty, nothing to process")
            return 0
        
        self.logger.info(f"[EMAIL] ===== QUEUE PROCESSING START =====")
        self.logger.info(f"[EMAIL] Processing {len(self._email_queue)} queued emails...")
        
        processed = 0
        failed = []
        permanently_failed = 0
        
        for email in self._email_queue:
            email_id = email.get('email_id', 'unknown')
            retry_count = email.get('retry_count', 0)
            
            self.logger.debug(f"[EMAIL] Processing queued email: {email_id} | retry #{retry_count + 1}")
            
            try:
                self._send_via_smtp(email)
                email['status'] = 'sent'
                email['sent_at'] = datetime.utcnow().isoformat()
                self._sent_emails.append(email)
                processed += 1
                self.logger.debug(f"[EMAIL] Queued email sent successfully: {email_id}")
                
            except Exception as e:
                email['retry_count'] = retry_count + 1
                email['last_error'] = str(e)
                
                if email['retry_count'] < 3:
                    failed.append(email)
                    self.logger.warning(f"[EMAIL] Retry failed for {email_id}: {str(e)} | will retry again (attempt {email['retry_count']}/3)")
                else:
                    email['status'] = 'permanently_failed'
                    self._sent_emails.append(email)
                    permanently_failed += 1
                    self.logger.error(f"[EMAIL] PERMANENTLY FAILED: {email_id} | max retries exceeded")
        
        self._email_queue = failed
        
        duration = (time.time() - start_time) * 1000
        
        self.logger.info(f"[EMAIL] Queue processing complete:")
        self.logger.info(f"[EMAIL]   Sent: {processed}")
        self.logger.info(f"[EMAIL]   Pending retry: {len(failed)}")
        self.logger.info(f"[EMAIL]   Permanently failed: {permanently_failed}")
        self.logger.info(f"[EMAIL]   Processing time: {duration:.2f}ms")
        self.logger.info(f"[EMAIL] ===== QUEUE PROCESSING END =====")
        
        return processed

