"""
Manual Logging Implementation
=============================
This module demonstrates what teams typically build without observability tools.
It includes structured logging, request/response tracking, and error formatting.

In a real-world scenario without Datadog, teams often:
- Build custom logging wrappers
- Add manual timing to every function
- Grep through log files for debugging
- Build dashboards from log aggregation tools
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Optional

# Custom formatter for structured logging
class StructuredFormatter(logging.Formatter):
    """
    Custom log formatter that outputs JSON-structured logs.
    Teams often build this to enable log parsing and aggregation.
    """
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add any extra fields
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_id'):
            log_entry['error_id'] = record.error_id
            
        return json.dumps(log_entry)


class SimpleFormatter(logging.Formatter):
    """
    Human-readable log format for development.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        timestamp = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
        
        base = f"{timestamp} {color}{record.levelname:8}{reset} | {record.getMessage()}"
        
        return base


def setup_logging(json_format: bool = False) -> logging.Logger:
    """
    Setup the application logger.
    
    Args:
        json_format: If True, output JSON logs. If False, human-readable.
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('tradesim')
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(SimpleFormatter())
    
    logger.addHandler(console_handler)
    
    return logger


def log_request(logger: logging.Logger, request_id: str, method: str, 
                path: str, body: Optional[dict] = None):
    """
    Log incoming request details.
    
    This is what teams manually add to track requests without APM.
    """
    # Sanitize body to not log sensitive data
    safe_body = None
    if body:
        safe_body = {k: v for k, v in body.items() if k not in ['password', 'token', 'secret']}
    
    logger.info(
        f"[REQ {request_id}] {method} {path}" + 
        (f" body={safe_body}" if safe_body else "")
    )


def log_response(logger: logging.Logger, request_id: str, 
                 status_code: int, duration_ms: float):
    """
    Log response details with timing.
    
    This is how teams manually track response times without APM.
    """
    level = logging.INFO
    status_indicator = "✓"
    
    if status_code >= 500:
        level = logging.ERROR
        status_indicator = "✗"
    elif status_code >= 400:
        level = logging.WARNING
        status_indicator = "!"
    
    # Log slow requests
    slow_indicator = ""
    if duration_ms > 1000:
        slow_indicator = " [SLOW]"
        level = logging.WARNING
    
    logger.log(
        level,
        f"[RES {request_id}] {status_indicator} {status_code} | {duration_ms:.2f}ms{slow_indicator}"
    )


def log_error(logger: logging.Logger, request_id: str, error_id: str, 
              error_message: str, path: str):
    """
    Log error details for debugging.
    
    Without Datadog, teams have to manually search logs for these error IDs.
    """
    logger.error(
        f"[ERR {request_id}] Error ID: {error_id} | Path: {path} | Message: {error_message}"
    )


def log_service_call(logger: logging.Logger, service_name: str, 
                     operation: str, duration_ms: float, success: bool,
                     details: Optional[dict] = None):
    """
    Log internal service calls with timing.
    
    This is the manual distributed tracing that teams build without APM.
    """
    status = "success" if success else "failed"
    level = logging.INFO if success else logging.ERROR
    
    message = f"[SVC] {service_name}.{operation} | {status} | {duration_ms:.2f}ms"
    
    if details:
        message += f" | {details}"
    
    logger.log(level, message)


def log_external_call(logger: logging.Logger, service_name: str, 
                      endpoint: str, method: str, status_code: int,
                      duration_ms: float):
    """
    Log calls to external services.
    
    Critical for debugging integration issues without APM.
    """
    level = logging.INFO if status_code < 400 else logging.ERROR
    
    logger.log(
        level,
        f"[EXT] {service_name} | {method} {endpoint} | {status_code} | {duration_ms:.2f}ms"
    )


class ServiceLogger:
    """
    Context manager for logging service operations with automatic timing.
    
    Usage:
        with ServiceLogger(logger, 'TradeService', 'execute_trade') as slog:
            # do work
            slog.add_detail('symbol', 'DDOG')
    """
    
    def __init__(self, logger: logging.Logger, service_name: str, operation: str):
        self.logger = logger
        self.service_name = service_name
        self.operation = operation
        self.start_time = None
        self.details = {}
        self.success = True
        
    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.utcnow() - self.start_time).total_seconds() * 1000
        
        if exc_type is not None:
            self.success = False
            self.details['error'] = str(exc_val)
        
        log_service_call(
            self.logger,
            self.service_name,
            self.operation,
            duration_ms,
            self.success,
            self.details if self.details else None
        )
        
        return False  # Don't suppress exceptions
    
    def add_detail(self, key: str, value: Any):
        self.details[key] = value
    
    def mark_failed(self):
        self.success = False

