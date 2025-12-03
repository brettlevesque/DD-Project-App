"""
Manual Metrics Collection
=========================
This module demonstrates what teams build to collect metrics without Datadog.

Typically, teams:
- Build custom counters and histograms
- Expose /metrics endpoints for Prometheus scraping
- Create dashboards from these raw metrics
- Manually track error rates, latency percentiles, etc.

This is error-prone and requires significant engineering investment.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics


class MetricsCollector:
    """
    A simple in-memory metrics collector.
    
    In production without Datadog, teams often use:
    - StatsD client libraries
    - Prometheus client libraries  
    - Custom solutions like this
    
    Problems with this approach:
    - Metrics are lost on restart
    - No automatic aggregation across instances
    - Manual instrumentation required
    - No auto-discovery of metrics
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._request_times: Dict[str, List[float]] = defaultdict(list)
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._status_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._recent_errors: List[Dict] = []
        self._service_calls: Dict[str, List[float]] = defaultdict(list)
        self._start_time = datetime.utcnow()
        
        # Custom business metrics
        self._trades_processed = 0
        self._trades_value = 0.0
        self._emails_sent = 0
        self._auth_attempts = 0
        self._auth_failures = 0
        
    def record_request(self, path: str, method: str, status_code: int, duration_ms: float):
        """Record an HTTP request"""
        with self._lock:
            key = f"{method}:{path}"
            self._request_times[key].append(duration_ms)
            self._request_counts[key] += 1
            self._status_counts[key][status_code] += 1
            
            # Keep only last 1000 measurements per endpoint (memory management)
            if len(self._request_times[key]) > 1000:
                self._request_times[key] = self._request_times[key][-1000:]
    
    def record_error(self, path: str, error_type: str):
        """Record an error"""
        with self._lock:
            key = f"{path}:{error_type}"
            self._error_counts[key] += 1
            
            # Store recent errors for debugging
            self._recent_errors.append({
                'timestamp': datetime.utcnow().isoformat(),
                'path': path,
                'error_type': error_type
            })
            
            # Keep only last 100 errors
            if len(self._recent_errors) > 100:
                self._recent_errors = self._recent_errors[-100:]
    
    def record_service_call(self, service: str, operation: str, duration_ms: float, success: bool):
        """Record an internal service call"""
        with self._lock:
            key = f"{service}.{operation}"
            self._service_calls[key].append(duration_ms)
            
            if not success:
                self._error_counts[f"service:{key}"] += 1
            
            # Keep only last 1000 measurements
            if len(self._service_calls[key]) > 1000:
                self._service_calls[key] = self._service_calls[key][-1000:]
    
    def record_trade(self, value: float):
        """Record a trade execution"""
        with self._lock:
            self._trades_processed += 1
            self._trades_value += value
    
    def record_email_sent(self):
        """Record email sent"""
        with self._lock:
            self._emails_sent += 1
    
    def record_auth_attempt(self, success: bool):
        """Record authentication attempt"""
        with self._lock:
            self._auth_attempts += 1
            if not success:
                self._auth_failures += 1
    
    def get_recent_errors(self) -> List[Dict]:
        """Get recent errors for debugging"""
        with self._lock:
            return list(self._recent_errors)
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._request_times.clear()
            self._request_counts.clear()
            self._error_counts.clear()
            self._status_counts.clear()
            self._recent_errors.clear()
            self._service_calls.clear()
            self._trades_processed = 0
            self._trades_value = 0.0
            self._emails_sent = 0
            self._auth_attempts = 0
            self._auth_failures = 0
            self._start_time = datetime.utcnow()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.
        
        This is what gets exposed at /metrics for monitoring tools to scrape.
        Without Datadog, teams have to manually interpret these numbers.
        """
        with self._lock:
            uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
            
            # Calculate endpoint statistics
            endpoint_stats = {}
            for key, times in self._request_times.items():
                if times:
                    endpoint_stats[key] = {
                        'count': self._request_counts[key],
                        'avg_ms': round(statistics.mean(times), 2),
                        'min_ms': round(min(times), 2),
                        'max_ms': round(max(times), 2),
                        'p50_ms': round(statistics.median(times), 2),
                        'p95_ms': round(self._percentile(times, 95), 2),
                        'p99_ms': round(self._percentile(times, 99), 2),
                        'status_codes': dict(self._status_counts[key])
                    }
            
            # Calculate service call statistics
            service_stats = {}
            for key, times in self._service_calls.items():
                if times:
                    service_stats[key] = {
                        'count': len(times),
                        'avg_ms': round(statistics.mean(times), 2),
                        'p95_ms': round(self._percentile(times, 95), 2),
                        'p99_ms': round(self._percentile(times, 99), 2)
                    }
            
            # Calculate error rate
            total_requests = sum(self._request_counts.values())
            total_errors = sum(v for k, v in self._error_counts.items() if not k.startswith('service:'))
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'uptime_seconds': round(uptime_seconds, 2),
                'uptime_human': str(timedelta(seconds=int(uptime_seconds))),
                'summary': {
                    'total_requests': total_requests,
                    'total_errors': total_errors,
                    'error_rate_percent': round(error_rate, 2),
                    'trades_processed': self._trades_processed,
                    'trades_total_value': round(self._trades_value, 2),
                    'emails_sent': self._emails_sent,
                    'auth_attempts': self._auth_attempts,
                    'auth_failure_rate': round(
                        (self._auth_failures / self._auth_attempts * 100) 
                        if self._auth_attempts > 0 else 0, 2
                    )
                },
                'endpoints': endpoint_stats,
                'services': service_stats,
                'errors': dict(self._error_counts)
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class Timer:
    """
    Context manager for timing operations.
    
    Usage:
        with Timer() as t:
            do_something()
        print(f"Took {t.duration_ms}ms")
    """
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration_ms = 0
        
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        return False


def timed(metrics: MetricsCollector, service: str, operation: str):
    """
    Decorator for timing service methods.
    
    Usage:
        @timed(metrics, 'TradeService', 'execute_trade')
        def execute_trade(self, ...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics.record_service_call(service, operation, duration_ms, success)
        return wrapper
    return decorator

