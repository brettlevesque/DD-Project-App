"""
Market Data Service
===================
Provides stock prices and market data.

Stock Configuration:
- Datadog (DDOG): Strong performer, steady growth
- Competitors (SPLK, DT, NEWR, ESTC): Poor performance
- Tech giants: Neutral to good performance
"""

import time
import random
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MarketService:
    """
    Provides market data for the trading platform.
    
    Stock behavior is configured to:
    - Make Datadog perform well (steady upward trend)
    - Make competitors perform poorly (downward/volatile)
    - Other stocks have realistic mixed performance
    """
    
    # Stock configurations with bias and realistic historical data
    STOCKS = {
        # Datadog - The hero 🚀
        'DDOG': {
            'name': 'Datadog, Inc.',
            'sector': 'Technology - Observability',
            'base_price': 135.00,
            'volatility': 0.012,  # Low volatility, stable
            'trend': 0.004,       # Strong upward trend (~1.2% daily)
            'description': 'The leading observability and security platform',
            # 90-day historical starting point (price 90 days ago)
            'history_start': 98.50,
        },
        
        # Competitors - Poor performers 📉
        'SPLK': {
            'name': 'Splunk Inc.',
            'sector': 'Technology - Observability',
            'base_price': 85.00,
            'volatility': 0.035,   # Higher volatility
            'trend': -0.003,       # Downward trend
            'description': 'Legacy log management platform',
            'history_start': 112.00,  # Started higher, declined
        },
        'DT': {
            'name': 'Dynatrace, Inc.',
            'sector': 'Technology - Observability',
            'base_price': 45.00,
            'volatility': 0.030,
            'trend': -0.002,       # Downward trend
            'description': 'Application performance monitoring',
            'history_start': 58.00,
        },
        'NEWR': {
            'name': 'New Relic, Inc.',
            'sector': 'Technology - Observability',
            'base_price': 68.00,
            'volatility': 0.040,   # High volatility
            'trend': -0.004,       # Strong downward trend
            'description': 'Observability platform',
            'history_start': 95.00,  # Big decline
        },
        'ESTC': {
            'name': 'Elastic N.V.',
            'sector': 'Technology - Search/Observability',
            'base_price': 72.00,
            'volatility': 0.032,
            'trend': -0.002,       # Slight downward
            'description': 'Search and observability platform',
            'history_start': 88.00,
        },
        
        # Tech giants - Generally stable/positive
        'AAPL': {
            'name': 'Apple Inc.',
            'sector': 'Technology - Consumer Electronics',
            'base_price': 189.00,
            'volatility': 0.015,
            'trend': 0.0012,
            'description': 'Consumer electronics and software',
            'history_start': 175.00,
        },
        'MSFT': {
            'name': 'Microsoft Corporation',
            'sector': 'Technology - Software',
            'base_price': 378.00,
            'volatility': 0.014,
            'trend': 0.0015,
            'description': 'Software and cloud computing',
            'history_start': 340.00,
        },
        'GOOGL': {
            'name': 'Alphabet Inc.',
            'sector': 'Technology - Internet',
            'base_price': 142.00,
            'volatility': 0.018,
            'trend': 0.001,
            'description': 'Internet services and products',
            'history_start': 132.00,
        },
        'AMZN': {
            'name': 'Amazon.com, Inc.',
            'sector': 'Technology - E-commerce/Cloud',
            'base_price': 178.00,
            'volatility': 0.020,
            'trend': 0.0008,
            'description': 'E-commerce and cloud computing',
            'history_start': 168.00,
        },
        'TSLA': {
            'name': 'Tesla, Inc.',
            'sector': 'Automotive - Electric Vehicles',
            'base_price': 245.00,
            'volatility': 0.045,   # High volatility
            'trend': 0.0,          # Neutral (wild swings)
            'description': 'Electric vehicles and clean energy',
            'history_start': 248.00,  # Basically flat with swings
        },
        'NVDA': {
            'name': 'NVIDIA Corporation',
            'sector': 'Technology - Semiconductors',
            'base_price': 495.00,
            'volatility': 0.028,
            'trend': 0.003,        # Upward trend (AI boom)
            'description': 'Graphics processing and AI chips',
            'history_start': 380.00,
        },
        'META': {
            'name': 'Meta Platforms, Inc.',
            'sector': 'Technology - Social Media',
            'base_price': 335.00,
            'volatility': 0.022,
            'trend': 0.001,
            'description': 'Social media and virtual reality',
            'history_start': 310.00,
        }
    }
    
    def __init__(self, logger, metrics):
        self.logger = logger
        self.metrics = metrics
        self._current_prices: Dict[str, float] = {}
        self._price_history: Dict[str, List[Dict]] = {}
        self._tick_count = 0
        
        self.logger.info(f"[MARKET] MarketService initializing with {len(self.STOCKS)} configured stocks...")
        
        # Initialize prices and history
        self._initialize_market()
        
    def _initialize_market(self):
        """Initialize market with base prices and generate history"""
        start_time = time.time()
        
        self.logger.info("[MARKET] ===== MARKET INITIALIZATION START =====")
        self.logger.info(f"[MARKET] Generating historical data for {len(self.STOCKS)} stocks...")
        
        for symbol, config in self.STOCKS.items():
            self._current_prices[symbol] = config['base_price']
            self._price_history[symbol] = []
            
            # Generate 90 days of historical data
            self._generate_history(symbol, 90)
            
            # Log individual stock initialization
            final_price = self._current_prices[symbol]
            history_start = config.get('history_start', config['base_price'] * 0.85)
            change_pct = ((final_price - history_start) / history_start) * 100
            self.logger.debug(f"[MARKET] Initialized {symbol}: ${history_start:.2f} -> ${final_price:.2f} ({change_pct:+.1f}%)")
        
        duration = (time.time() - start_time) * 1000
        
        # Log summary by category
        ddog_price = self._current_prices.get('DDOG', 0)
        competitors = ['SPLK', 'DT', 'NEWR', 'ESTC']
        comp_prices = [self._current_prices.get(s, 0) for s in competitors]
        
        self.logger.info(f"[MARKET] Initialization complete | stocks={len(self.STOCKS)} | {duration:.2f}ms")
        self.logger.info(f"[MARKET] DDOG (hero): ${ddog_price:.2f}")
        self.logger.info(f"[MARKET] Competitors: SPLK=${self._current_prices.get('SPLK', 0):.2f}, DT=${self._current_prices.get('DT', 0):.2f}, NEWR=${self._current_prices.get('NEWR', 0):.2f}, ESTC=${self._current_prices.get('ESTC', 0):.2f}")
        self.logger.info("[MARKET] ===== MARKET INITIALIZATION END =====")
    
    def _generate_history(self, symbol: str, days: int):
        """Generate realistic historical price data following configured trends"""
        config = self.STOCKS[symbol]
        
        # Start from the configured historical starting point
        start_price = config.get('history_start', config['base_price'] * 0.85)
        target_price = config['base_price']
        
        # Calculate the daily drift needed to get from start to target
        # while still applying volatility
        total_return = (target_price - start_price) / start_price
        daily_drift = total_return / days
        
        price = start_price
        prices = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - i)
            
            # Add the day's data point
            # For intraday variation, add open, high, low, close
            daily_volatility = config['volatility']
            
            # Calculate this day's movement
            random_component = random.gauss(0, daily_volatility)
            trend_component = daily_drift + config['trend']
            
            # Apply movement
            day_return = trend_component + random_component
            new_price = price * (1 + day_return)
            new_price = max(new_price, 1.0)  # Floor at $1
            
            # Generate OHLC data
            open_price = price
            close_price = new_price
            
            # High and low within the day
            intraday_range = abs(new_price - price) + (price * daily_volatility * 0.5)
            high_price = max(open_price, close_price) + random.uniform(0, intraday_range * 0.5)
            low_price = min(open_price, close_price) - random.uniform(0, intraday_range * 0.5)
            low_price = max(low_price, 1.0)
            
            # Volume varies with volatility and trend
            base_volume = random.randint(5000000, 15000000)
            volume_multiplier = 1 + abs(day_return) * 10  # Higher volume on big move days
            volume = int(base_volume * volume_multiplier)
            
            self._price_history[symbol].append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'price': round(close_price, 2),  # Keep for backward compatibility
                'volume': volume,
                'change': round(close_price - open_price, 2),
                'change_pct': round((close_price - open_price) / open_price * 100, 2)
            })
            
            price = new_price
            prices.append(price)
        
        # Set current price to the final historical price
        self._current_prices[symbol] = round(price, 2)
        
        # Log the stock's performance
        total_change = ((price - start_price) / start_price) * 100
        self.logger.debug(f"[MARKET] {symbol}: ${start_price:.2f} -> ${price:.2f} ({total_change:+.1f}% over {days} days)")
    
    def health_check(self) -> Dict:
        """Check if market service is healthy"""
        try:
            # Calculate market statistics
            total_history_points = sum(len(h) for h in self._price_history.values())
            avg_price = sum(self._current_prices.values()) / len(self._current_prices) if self._current_prices else 0
            
            status = {
                'status': 'healthy',
                'stocks_available': len(self.STOCKS),
                'last_tick': self._tick_count,
                'total_history_points': total_history_points,
                'avg_price': round(avg_price, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.debug(f"[MARKET] Health check: {len(self.STOCKS)} stocks, {self._tick_count} ticks, {total_history_points} history points")
            return status
            
        except Exception as e:
            self.logger.error(f"[MARKET] Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_all_stocks(self) -> List[Dict]:
        """Get all available stocks with current prices"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[MARKET] Fetching all stocks data...")
            
            stocks = []
            gainers = 0
            losers = 0
            
            for symbol, config in self.STOCKS.items():
                current_price = self._current_prices[symbol]
                
                # Calculate daily change from history
                history = self._price_history.get(symbol, [])
                if len(history) >= 2:
                    prev_close = history[-2]['close']
                    daily_change = current_price - prev_close
                    daily_change_pct = (daily_change / prev_close) * 100
                else:
                    daily_change = 0
                    daily_change_pct = 0
                
                # Track gainers/losers
                if daily_change > 0:
                    gainers += 1
                elif daily_change < 0:
                    losers += 1
                
                # Calculate overall performance (from history start)
                if history:
                    start_price = history[0]['open']
                    total_change = current_price - start_price
                    total_change_pct = (total_change / start_price) * 100
                else:
                    total_change = 0
                    total_change_pct = 0
                
                stocks.append({
                    'symbol': symbol,
                    'name': config['name'],
                    'sector': config['sector'],
                    'price': round(current_price, 2),
                    'daily_change': round(daily_change, 2),
                    'daily_change_pct': round(daily_change_pct, 2),
                    'total_change': round(total_change, 2),
                    'total_change_pct': round(total_change_pct, 2),
                    'description': config['description']
                })
            
            # Sort by symbol
            stocks.sort(key=lambda x: x['symbol'])
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.debug(f"[MARKET] All stocks fetched: count={len(stocks)} | gainers={gainers} | losers={losers} | flat={len(stocks)-gainers-losers} | {duration:.2f}ms")
            self.metrics.record_service_call('MarketService', 'get_all_stocks', duration, True)
            
            return stocks
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[MARKET] Failed to get all stocks: {str(e)} | {duration:.2f}ms")
            self.logger.error(f"[MARKET] Traceback: {traceback.format_exc()}")
            self.metrics.record_service_call('MarketService', 'get_all_stocks', duration, False)
            return []
    
    def get_stock(self, symbol: str) -> Optional[Dict]:
        """Get specific stock data with full details"""
        start_time = time.time()
        
        try:
            self.logger.debug(f"[MARKET] Fetching stock data for: {symbol}")
            
            config = self.STOCKS.get(symbol)
            if not config:
                self.logger.warning(f"[MARKET] Stock not found: {symbol}")
                return None
            
            current_price = self._current_prices[symbol]
            history = self._price_history.get(symbol, [])
            
            if len(history) >= 2:
                prev_close = history[-2]['close']
                daily_change = current_price - prev_close
                daily_change_pct = (daily_change / prev_close) * 100
            else:
                daily_change = 0
                daily_change_pct = 0
            
            # Calculate performance metrics
            if history:
                start_price = history[0]['open']
                high_52w = max(h['high'] for h in history)
                low_52w = min(h['low'] for h in history)
                avg_volume = sum(h['volume'] for h in history) / len(history)
                total_change_pct = ((current_price - start_price) / start_price) * 100
            else:
                start_price = current_price
                high_52w = current_price
                low_52w = current_price
                avg_volume = 0
                total_change_pct = 0
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.debug(f"[MARKET] Stock data retrieved: {symbol} | price=${current_price:.2f} | daily={daily_change_pct:+.2f}% | total={total_change_pct:+.1f}% | {duration:.2f}ms")
            self.metrics.record_service_call('MarketService', 'get_stock', duration, True)
            
            return {
                'symbol': symbol,
                'name': config['name'],
                'sector': config['sector'],
                'price': round(current_price, 2),
                'daily_change': round(daily_change, 2),
                'daily_change_pct': round(daily_change_pct, 2),
                'description': config['description'],
                'volatility': config['volatility'],
                'high_52w': round(high_52w, 2),
                'low_52w': round(low_52w, 2),
                'avg_volume': int(avg_volume),
                'market_cap': round(current_price * random.randint(100000000, 500000000), 0)
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[MARKET] Failed to get stock {symbol}: {str(e)} | {duration:.2f}ms")
            self.metrics.record_service_call('MarketService', 'get_stock', duration, False)
            return None
    
    def get_price_history(self, symbol: str, days: int = 30) -> Optional[List[Dict]]:
        """Get stock price history with OHLC data"""
        try:
            if symbol not in self.STOCKS:
                self.logger.warning(f"[MARKET] Price history requested for unknown symbol: {symbol}")
                return None
            
            history = self._price_history.get(symbol, [])
            result = history[-days:] if days < len(history) else history
            
            if result:
                start_price = result[0].get('open', 0)
                end_price = result[-1].get('close', 0)
                period_change = ((end_price - start_price) / start_price * 100) if start_price > 0 else 0
                
                self.logger.debug(f"[MARKET] Price history retrieved: symbol={symbol} | days={len(result)} | {start_price:.2f} -> {end_price:.2f} ({period_change:+.1f}%)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"[MARKET] Failed to get price history for {symbol}: {str(e)}")
            return None
    
    def simulate_market_tick(self):
        """
        Simulate market movement (call periodically).
        
        This applies the configured trends and volatility to all stocks.
        """
        start_time = time.time()
        self._tick_count += 1
        
        try:
            self.logger.debug(f"[MARKET] ===== MARKET TICK #{self._tick_count} START =====")
            
            big_movers = []  # Track stocks with >1% move
            
            for symbol, config in self.STOCKS.items():
                current_price = self._current_prices[symbol]
                
                # Apply trend + random movement
                change = random.gauss(config['trend'], config['volatility'])
                new_price = current_price * (1 + change)
                new_price = max(new_price, 1.0)  # Floor at $1
                
                price_change = new_price - current_price
                price_change_pct = (price_change / current_price) * 100
                
                self._current_prices[symbol] = round(new_price, 2)
                
                # Track big movers
                if abs(price_change_pct) > 1.0:
                    big_movers.append(f"{symbol}: {price_change_pct:+.2f}%")
                
                # Update today's history entry
                today = datetime.utcnow().strftime('%Y-%m-%d')
                if self._price_history[symbol] and self._price_history[symbol][-1]['date'] == today:
                    # Update today's entry
                    entry = self._price_history[symbol][-1]
                    entry['close'] = round(new_price, 2)
                    entry['price'] = round(new_price, 2)
                    entry['high'] = max(entry['high'], new_price)
                    entry['low'] = min(entry['low'], new_price)
                    entry['change'] = round(new_price - entry['open'], 2)
                    entry['change_pct'] = round((new_price - entry['open']) / entry['open'] * 100, 2)
                else:
                    # Add new day
                    prev_close = self._price_history[symbol][-1]['close'] if self._price_history[symbol] else current_price
                    self._price_history[symbol].append({
                        'date': today,
                        'open': round(prev_close, 2),
                        'high': round(max(prev_close, new_price), 2),
                        'low': round(min(prev_close, new_price), 2),
                        'close': round(new_price, 2),
                        'price': round(new_price, 2),
                        'volume': random.randint(5000000, 15000000),
                        'change': round(new_price - prev_close, 2),
                        'change_pct': round((new_price - prev_close) / prev_close * 100, 2)
                    })
                    self.logger.debug(f"[MARKET] New trading day started for {symbol}")
            
            duration = (time.time() - start_time) * 1000
            
            # Log tick summary
            ddog_price = self._current_prices.get('DDOG', 0)
            self.logger.debug(f"[MARKET] Tick #{self._tick_count} complete | stocks={len(self.STOCKS)} | DDOG=${ddog_price:.2f} | {duration:.2f}ms")
            
            if big_movers:
                self.logger.debug(f"[MARKET] Big movers this tick: {', '.join(big_movers)}")
            
            self.logger.debug(f"[MARKET] ===== MARKET TICK #{self._tick_count} END =====")
            
            self.metrics.record_service_call('MarketService', 'simulate_market_tick', duration, True)
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.error(f"[MARKET] Tick #{self._tick_count} FAILED: {str(e)} | {duration:.2f}ms")
            self.logger.error(f"[MARKET] Traceback: {traceback.format_exc()}")
            self.metrics.record_service_call('MarketService', 'simulate_market_tick', duration, False)
    
    def get_market_summary(self) -> Dict:
        """Get market summary statistics"""
        start_time = time.time()
        
        try:
            self.logger.debug("[MARKET] Generating market summary...")
            
            gainers = []
            losers = []
            unchanged = 0
            
            for symbol in self.STOCKS:
                stock = self.get_stock(symbol)
                if stock:
                    if stock['daily_change'] > 0:
                        gainers.append(stock)
                    elif stock['daily_change'] < 0:
                        losers.append(stock)
                    else:
                        unchanged += 1
            
            gainers.sort(key=lambda x: x['daily_change_pct'], reverse=True)
            losers.sort(key=lambda x: x['daily_change_pct'])
            
            duration = (time.time() - start_time) * 1000
            
            self.logger.debug(f"[MARKET] Market summary: gainers={len(gainers)} | losers={len(losers)} | unchanged={unchanged} | {duration:.2f}ms")
            
            if gainers:
                top = gainers[0]
                self.logger.debug(f"[MARKET] Top gainer: {top['symbol']} ({top['daily_change_pct']:+.2f}%)")
            if losers:
                bottom = losers[0]
                self.logger.debug(f"[MARKET] Top loser: {bottom['symbol']} ({bottom['daily_change_pct']:+.2f}%)")
            
            return {
                'top_gainers': gainers[:3],
                'top_losers': losers[:3],
                'total_stocks': len(self.STOCKS),
                'advancing': len(gainers),
                'declining': len(losers),
                'unchanged': unchanged,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"[MARKET] Failed to generate market summary: {str(e)}")
            self.logger.error(f"[MARKET] Traceback: {traceback.format_exc()}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
