"""
TradeSim - A Trading Platform Demo Without Observability Tooling
================================================================
This application demonstrates the challenges of monitoring and debugging
a distributed application without proper observability tools.

Manual observability patterns used:
- Request timing with decorators
- Correlation IDs for request tracing
- Structured logging to console/file
- Health check endpoints
- Error counting and tracking
- Performance metrics collection
"""

import os
import time
import uuid
import random
import logging
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g
from flask_cors import CORS

# Import our services
from services.auth_service import AuthService
from services.trade_service import TradeService
from services.fund_service import FundService
from services.email_service import EmailService
from services.market_service import MarketService
from services.portfolio_service import PortfolioService
from observability.logger import setup_logging, log_request, log_response, log_error
from observability.metrics import MetricsCollector

# ============================================
# APPLICATION SETUP
# ============================================

app = Flask(__name__)
CORS(app)

# Setup manual logging (what teams do without Datadog)
logger = setup_logging()
metrics = MetricsCollector()

# Initialize services
auth_service = AuthService(logger, metrics)
trade_service = TradeService(logger, metrics)
fund_service = FundService(logger, metrics)
email_service = EmailService(logger, metrics)
market_service = MarketService(logger, metrics)
portfolio_service = PortfolioService(logger, metrics)

# ============================================
# MANUAL OBSERVABILITY MIDDLEWARE
# ============================================

@app.before_request
def before_request():
    """Manual request tracking - what teams do without APM"""
    g.request_id = str(uuid.uuid4())[:8]
    g.start_time = time.time()
    
    # Manual request logging
    log_request(logger, g.request_id, request.method, request.path, request.get_json(silent=True))

@app.after_request
def after_request(response):
    """Manual response tracking and timing"""
    duration_ms = (time.time() - g.start_time) * 1000
    
    # Manual metrics collection
    metrics.record_request(request.path, request.method, response.status_code, duration_ms)
    
    # Manual response logging
    log_response(logger, g.request_id, response.status_code, duration_ms)
    
    # Add correlation ID to response headers (manual tracing)
    response.headers['X-Request-ID'] = g.request_id
    response.headers['X-Response-Time-Ms'] = str(round(duration_ms, 2))
    
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Manual error handling and logging"""
    error_id = str(uuid.uuid4())[:8]
    duration_ms = (time.time() - g.start_time) * 1000 if hasattr(g, 'start_time') else 0
    
    log_error(logger, g.request_id if hasattr(g, 'request_id') else 'unknown', 
              error_id, str(e), request.path)
    
    metrics.record_error(request.path, type(e).__name__)
    
    return jsonify({
        'error': str(e),
        'error_id': error_id,
        'request_id': g.request_id if hasattr(g, 'request_id') else 'unknown',
        'message': 'An error occurred. Please reference error_id when contacting support.'
    }), 500

# ============================================
# HEALTH & METRICS ENDPOINTS (Manual Monitoring)
# ============================================

@app.route('/health', methods=['GET'])
def health_check():
    """Manual health check endpoint - teams poll this with scripts"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'auth': auth_service.health_check(),
            'trade': trade_service.health_check(),
            'fund': fund_service.health_check(),
            'email': email_service.health_check(),
            'market': market_service.health_check(),
            'portfolio': portfolio_service.health_check()
        }
    }
    
    # Manual: Check if any service is unhealthy
    all_healthy = all(s['status'] == 'healthy' for s in health_status['services'].values())
    
    if not all_healthy:
        logger.warning(f"[HEALTH] Some services are unhealthy: {health_status['services']}")
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Manual metrics endpoint - what Prometheus scrapes, but without auto-instrumentation"""
    return jsonify(metrics.get_all_metrics()), 200

@app.route('/metrics/reset', methods=['POST'])
def reset_metrics():
    """Reset metrics - useful for demos"""
    metrics.reset()
    return jsonify({'status': 'metrics reset'}), 200

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return session token"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'error': 'Username required'}), 400
    
    result = auth_service.login(data['username'], data.get('password', ''))
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@app.route('/api/auth/validate', methods=['POST'])
def validate_session():
    """Validate session token"""
    data = request.get_json()
    
    if not data or 'token' not in data:
        return jsonify({'error': 'Token required'}), 400
    
    result = auth_service.validate_token(data['token'])
    return jsonify(result), 200 if result['valid'] else 401

# ============================================
# PORTFOLIO ENDPOINTS
# ============================================

@app.route('/api/portfolio/<user_id>', methods=['GET'])
def get_portfolio(user_id):
    """Get user's portfolio"""
    portfolio = portfolio_service.get_portfolio(user_id)
    return jsonify(portfolio), 200

@app.route('/api/portfolio/<user_id>/balance', methods=['POST'])
def set_balance(user_id):
    """Set user's cash balance"""
    data = request.get_json()
    
    if not data or 'balance' not in data:
        return jsonify({'error': 'Balance required'}), 400
    
    balance = data['balance']
    
    # Sync balance across services (this is a common issue without proper tooling!)
    result = portfolio_service.set_balance(user_id, balance)
    fund_service.set_balance(user_id, balance)  # Keep fund service in sync
    
    return jsonify(result), 200

# ============================================
# MARKET DATA ENDPOINTS
# ============================================

@app.route('/api/market/stocks', methods=['GET'])
def get_all_stocks():
    """Get all available stocks with current prices"""
    stocks = market_service.get_all_stocks()
    return jsonify({'stocks': stocks}), 200

@app.route('/api/market/stocks/<symbol>', methods=['GET'])
def get_stock(symbol):
    """Get specific stock data"""
    stock = market_service.get_stock(symbol.upper())
    
    if stock:
        return jsonify(stock), 200
    else:
        return jsonify({'error': f'Stock {symbol} not found'}), 404

@app.route('/api/market/stocks/<symbol>/history', methods=['GET'])
def get_stock_history(symbol):
    """Get stock price history"""
    days = request.args.get('days', 30, type=int)
    history = market_service.get_price_history(symbol.upper(), days)
    
    if history:
        return jsonify({'symbol': symbol.upper(), 'history': history}), 200
    else:
        return jsonify({'error': f'Stock {symbol} not found'}), 404

@app.route('/api/market/history/all', methods=['GET'])
def get_all_stock_histories():
    """Get price history for all stocks (for mini charts)"""
    days = request.args.get('days', 30, type=int)
    histories = {}
    
    for symbol in market_service.STOCKS.keys():
        history = market_service.get_price_history(symbol, days)
        if history:
            # Return simplified data for mini charts (just close prices)
            histories[symbol] = [h['close'] for h in history]
    
    return jsonify({'histories': histories, 'days': days}), 200

@app.route('/api/market/tick', methods=['POST'])
def market_tick():
    """Simulate market movement"""
    market_service.simulate_market_tick()
    return jsonify({'status': 'market updated'}), 200

# ============================================
# TRADING ENDPOINTS
# ============================================

@app.route('/api/trade/buy', methods=['POST'])
def buy_stock():
    """
    Execute a buy order
    This endpoint orchestrates multiple services (like a real trading system):
    1. Validate user session
    2. Check stock availability
    3. Verify funds
    4. Process trade
    5. Send confirmation email
    """
    data = request.get_json()
    
    required_fields = ['user_id', 'symbol', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    user_id = data['user_id']
    symbol = data['symbol'].upper()
    quantity = int(data['quantity'])
    
    # Step 1: Get current stock price
    stock = market_service.get_stock(symbol)
    if not stock:
        return jsonify({'error': f'Stock {symbol} not found'}), 404
    
    total_cost = stock['price'] * quantity
    
    # Step 2: Verify user has sufficient funds
    fund_check = fund_service.verify_funds(user_id, total_cost)
    if not fund_check['sufficient']:
        logger.warning(f"[TRADE] Insufficient funds for user {user_id}: needed ${total_cost}, has ${fund_check['available']}")
        return jsonify({
            'error': 'Insufficient funds',
            'required': total_cost,
            'available': fund_check['available']
        }), 400
    
    # Step 3: Authenticate the bank transfer
    auth_result = fund_service.authenticate_transfer(user_id, total_cost, 'buy')
    if not auth_result['authenticated']:
        return jsonify({'error': 'Bank transfer authentication failed'}), 401
    
    # Step 4: Process the trade
    trade_result = trade_service.execute_trade(user_id, symbol, quantity, stock['price'], 'buy')
    
    if trade_result['success']:
        # Step 5: Update portfolio
        portfolio_service.add_position(user_id, symbol, quantity, stock['price'])
        portfolio_service.deduct_balance(user_id, total_cost)
        fund_service.deduct_balance(user_id, total_cost)  # Keep fund service in sync
        
        # Step 6: Send confirmation email
        email_service.send_trade_confirmation(user_id, trade_result['trade'])
        
        return jsonify(trade_result), 200
    else:
        return jsonify(trade_result), 500

@app.route('/api/trade/sell', methods=['POST'])
def sell_stock():
    """Execute a sell order"""
    data = request.get_json()
    
    required_fields = ['user_id', 'symbol', 'quantity']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    user_id = data['user_id']
    symbol = data['symbol'].upper()
    quantity = int(data['quantity'])
    
    # Step 1: Check if user owns enough shares
    position = portfolio_service.get_position(user_id, symbol)
    if not position or position['quantity'] < quantity:
        return jsonify({
            'error': 'Insufficient shares',
            'requested': quantity,
            'available': position['quantity'] if position else 0
        }), 400
    
    # Step 2: Get current stock price
    stock = market_service.get_stock(symbol)
    if not stock:
        return jsonify({'error': f'Stock {symbol} not found'}), 404
    
    total_value = stock['price'] * quantity
    
    # Step 3: Authenticate the bank transfer
    auth_result = fund_service.authenticate_transfer(user_id, total_value, 'sell')
    if not auth_result['authenticated']:
        return jsonify({'error': 'Bank transfer authentication failed'}), 401
    
    # Step 4: Process the trade
    trade_result = trade_service.execute_trade(user_id, symbol, quantity, stock['price'], 'sell')
    
    if trade_result['success']:
        # Step 5: Update portfolio
        portfolio_service.reduce_position(user_id, symbol, quantity)
        portfolio_service.add_balance(user_id, total_value)
        fund_service.add_balance(user_id, total_value)  # Keep fund service in sync
        
        # Step 6: Send confirmation email
        email_service.send_trade_confirmation(user_id, trade_result['trade'])
        
        return jsonify(trade_result), 200
    else:
        return jsonify(trade_result), 500

@app.route('/api/trade/history/<user_id>', methods=['GET'])
def get_trade_history(user_id):
    """Get user's trade history"""
    history = trade_service.get_trade_history(user_id)
    return jsonify({'trades': history}), 200

# ============================================
# DEBUG ENDPOINTS (For Demo Purposes)
# ============================================

@app.route('/api/debug/slow', methods=['GET'])
def slow_endpoint():
    """Simulate a slow endpoint to demonstrate timing issues"""
    delay = random.uniform(1, 3)
    time.sleep(delay)
    logger.warning(f"[PERF] Slow endpoint took {delay:.2f}s")
    return jsonify({'status': 'slow response', 'delay_seconds': delay}), 200

@app.route('/api/debug/error', methods=['GET'])
def error_endpoint():
    """Simulate an error to demonstrate error tracking"""
    error_type = request.args.get('type', 'generic')
    
    if error_type == 'db':
        raise Exception("Database connection timeout after 30s")
    elif error_type == 'external':
        raise Exception("External API returned 503 Service Unavailable")
    elif error_type == 'validation':
        raise ValueError("Invalid input: negative quantity not allowed")
    else:
        raise Exception("Something went wrong!")

@app.route('/api/debug/logs', methods=['GET'])
def get_recent_logs():
    """Get recent log entries (simulating what teams grep for)"""
    # In reality, teams would be tailing log files or searching Elasticsearch
    return jsonify({
        'message': 'In production, you would grep through log files or search Elasticsearch',
        'sample_command': 'tail -f /var/log/tradesim/app.log | grep ERROR',
        'recent_errors': metrics.get_recent_errors()
    }), 200

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("TradeSim Platform Starting")
    logger.info("=" * 60)
    logger.info("Manual observability mode - No APM tooling installed")
    logger.info("Using: Custom logging, timing decorators, health checks")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

