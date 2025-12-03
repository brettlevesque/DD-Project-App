/**
 * TradeSim - Frontend Application
 * ================================
 * A trading platform demo to showcase the challenges of 
 * monitoring applications without proper observability tools.
 */

// ============================================
// Configuration
// ============================================

const CONFIG = {
    API_BASE: 'http://localhost:5000',
    USER_ID: 'demo',
    REFRESH_INTERVAL: 1000, // 30 seconds
    TICK_INTERVAL: 1000,     // 1 second auto-tick
    COMPETITOR_SYMBOLS: ['SPLK', 'DT', 'NEWR', 'ESTC']
};

// ============================================
// State Management
// ============================================

const state = {
    stocks: [],
    stockHistories: {},  // symbol -> array of prices for mini charts
    portfolio: null,
    trades: [],
    selectedStock: null,
    selectedStockHistory: null,
    tradeType: 'buy',
    logs: [],
    connected: false
};

// ============================================
// DOM Elements
// ============================================

const elements = {
    // Portfolio
    portfolioValue: document.getElementById('portfolioValue'),
    cashBalance: document.getElementById('cashBalance'),
    positionsValue: document.getElementById('positionsValue'),
    positionsList: document.getElementById('positionsList'),
    userBalance: document.getElementById('userBalance'),
    
    // Market
    stockGrid: document.getElementById('stockGrid'),
    connectionStatus: document.getElementById('connectionStatus'),
    
    // Activity
    tradesList: document.getElementById('tradesList'),
    logsList: document.getElementById('logsList'),
    
    // Modals
    tradeModal: document.getElementById('tradeModal'),
    balanceModal: document.getElementById('balanceModal'),
    metricsModal: document.getElementById('metricsModal'),
    
    // Trade Modal Elements
    modalSymbol: document.getElementById('modalSymbol'),
    modalStockName: document.getElementById('modalStockName'),
    modalPrice: document.getElementById('modalPrice'),
    modalChange: document.getElementById('modalChange'),
    quantity: document.getElementById('quantity'),
    pricePerShare: document.getElementById('pricePerShare'),
    quantityDisplay: document.getElementById('quantityDisplay'),
    estimatedTotal: document.getElementById('estimatedTotal'),
    availableFunds: document.getElementById('availableFunds'),
    sharesOwnedRow: document.getElementById('sharesOwnedRow'),
    sharesOwned: document.getElementById('sharesOwned'),
    buyBtn: document.getElementById('buyBtn'),
    sellBtn: document.getElementById('sellBtn'),
    executeTrade: document.getElementById('executeTrade'),
    chartContainer: document.getElementById('chartContainer'),
    chartPerformance: document.getElementById('chartPerformance'),
    
    // Other
    metricsGrid: document.getElementById('metricsGrid'),
    newBalance: document.getElementById('newBalance')
};

// ============================================
// Logging Utility
// ============================================

function log(message, level = 'info') {
    const entry = {
        timestamp: new Date().toISOString(),
        message,
        level
    };
    
    state.logs.unshift(entry);
    
    // Keep only last 100 logs
    if (state.logs.length > 100) {
        state.logs = state.logs.slice(0, 100);
    }
    
    renderLogs();
    
    // Console output
    const prefix = `[${new Date().toLocaleTimeString()}]`;
    switch(level) {
        case 'success':
            console.log(`%c${prefix} ${message}`, 'color: #10b981');
            break;
        case 'warning':
            console.warn(`${prefix} ${message}`);
            break;
        case 'error':
            console.error(`${prefix} ${message}`);
            break;
        default:
            console.log(`${prefix} ${message}`);
    }
}

// ============================================
// API Functions
// ============================================

async function apiCall(endpoint, options = {}) {
    const startTime = performance.now();
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const duration = Math.round(performance.now() - startTime);
        
        // Update connection status
        updateConnectionStatus(true);
        
        // Log request timing (manual observability)
        log(`API ${options.method || 'GET'} ${endpoint} - ${response.status} (${duration}ms)`, 
            response.ok ? 'info' : 'warning');
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API Error');
        }
        
        return data;
    } catch (error) {
        const duration = Math.round(performance.now() - startTime);
        
        // Check if it's a connection error
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            updateConnectionStatus(false);
            log(`API ${options.method || 'GET'} ${endpoint} - CONNECTION FAILED (${duration}ms)`, 'error');
        } else {
            log(`API ${options.method || 'GET'} ${endpoint} - ERROR: ${error.message} (${duration}ms)`, 'error');
        }
        throw error;
    }
}

function updateConnectionStatus(connected) {
    state.connected = connected;
    const statusEl = elements.connectionStatus;
    
    if (connected) {
        statusEl.classList.add('connected');
        statusEl.innerHTML = '<span class="status-dot"></span><span>Connected</span>';
    } else {
        statusEl.classList.remove('connected');
        statusEl.innerHTML = '<span class="status-dot error"></span><span>Backend Offline</span>';
    }
}

// ============================================
// Data Fetching
// ============================================

async function fetchStocks() {
    try {
        const data = await apiCall('/api/market/stocks');
        state.stocks = data.stocks;
        renderStocks();
    } catch (error) {
        elements.stockGrid.innerHTML = `
            <div class="empty-state">
                <strong>Cannot connect to backend</strong><br>
                <small>Make sure to run: cd backend && python app.py</small>
            </div>
        `;
    }
}

async function fetchAllStockHistories() {
    try {
        const data = await apiCall('/api/market/history/all?days=30');
        state.stockHistories = data.histories;
        console.log('Stock histories loaded:', Object.keys(state.stockHistories).length, 'stocks');
        console.log('Sample DDOG history:', state.stockHistories['DDOG']?.slice(0, 5));
        renderStocks(); // Re-render with charts
    } catch (error) {
        log(`Failed to fetch stock histories: ${error.message}`, 'warning');
    }
}

async function fetchStockHistory(symbol) {
    try {
        const data = await apiCall(`/api/market/stocks/${symbol}/history?days=90`);
        return data.history;
    } catch (error) {
        log(`Failed to fetch history for ${symbol}: ${error.message}`, 'error');
        return null;
    }
}

async function fetchPortfolio() {
    try {
        const data = await apiCall(`/api/portfolio/${CONFIG.USER_ID}`);
        state.portfolio = data;
        renderPortfolio();
    } catch (error) {
        log(`Failed to fetch portfolio: ${error.message}`, 'error');
    }
}

async function fetchTradeHistory() {
    try {
        const data = await apiCall(`/api/trade/history/${CONFIG.USER_ID}`);
        state.trades = data.trades || [];
        renderTrades();
    } catch (error) {
        log(`Failed to fetch trade history: ${error.message}`, 'error');
    }
}

async function setBalance(amount) {
    try {
        await apiCall(`/api/portfolio/${CONFIG.USER_ID}/balance`, {
            method: 'POST',
            body: JSON.stringify({ balance: amount })
        });
        log(`Balance set to $${amount.toLocaleString()}`, 'success');
        await fetchPortfolio();
    } catch (error) {
        log(`Failed to set balance: ${error.message}`, 'error');
    }
}

async function executeTrade() {
    const stock = state.selectedStock;
    const quantity = parseInt(elements.quantity.value);
    const side = state.tradeType;
    
    if (!stock || quantity <= 0) {
        log('Invalid trade parameters', 'error');
        return;
    }
    
    try {
        elements.executeTrade.disabled = true;
        elements.executeTrade.innerHTML = '<span class="btn-icon">⏳</span> Processing...';
        
        const endpoint = `/api/trade/${side}`;
        const data = await apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify({
                user_id: CONFIG.USER_ID,
                symbol: stock.symbol,
                quantity: quantity
            })
        });
        
        log(`✓ ${side.toUpperCase()} ${quantity} ${stock.symbol} @ $${stock.price.toFixed(2)}`, 'success');
        
        closeTradeModal();
        await Promise.all([fetchPortfolio(), fetchTradeHistory()]);
        
    } catch (error) {
        log(`Trade failed: ${error.message}`, 'error');
        alert(`Trade failed: ${error.message}`);
    } finally {
        elements.executeTrade.disabled = false;
        updateExecuteButton();
    }
}

async function simulateMarketTick() {
    try {
        await apiCall('/api/market/tick', { method: 'POST' });
        log('⚡ Market tick simulated', 'success');
        await fetchStocks();
        renderPortfolio(); // Update position values
    } catch (error) {
        log(`Market tick failed: ${error.message}`, 'error');
    }
}

async function fetchMetrics() {
    try {
        const data = await apiCall('/metrics');
        renderMetrics(data);
    } catch (error) {
        elements.metricsGrid.innerHTML = `
            <div class="empty-state">Failed to load metrics: ${error.message}</div>
        `;
    }
}

// ============================================
// Rendering Functions
// ============================================

function renderStocks() {
    if (!state.stocks.length) {
        elements.stockGrid.innerHTML = '<div class="empty-state">No stocks available</div>';
        return;
    }
    
    elements.stockGrid.innerHTML = state.stocks.map(stock => {
        const isDatadog = stock.symbol === 'DDOG';
        const isCompetitor = CONFIG.COMPETITOR_SYMBOLS.includes(stock.symbol);
        const totalChangeClass = stock.total_change_pct >= 0 ? 'positive' : 'negative';
        const changeIcon = stock.total_change_pct >= 0 ? '▲' : '▼';
        
        // Generate the chart for the card background
        const chartSvg = generateCardChart(stock.symbol, stock.total_change_pct >= 0);
        
        return `
            <div class="stock-card ${isDatadog ? 'datadog' : ''} ${isCompetitor ? 'competitor' : ''}" 
                 onclick="openTradeModal('${stock.symbol}')">
                
                <div class="stock-card-chart-bg">
                    ${chartSvg}
                </div>
                
                <div class="stock-card-overlay">
                    <div class="stock-card-top">
                        <span class="stock-symbol">${stock.symbol}</span>
                        <span class="stock-change-badge ${totalChangeClass}">
                            ${changeIcon} ${stock.total_change_pct >= 0 ? '+' : ''}${stock.total_change_pct.toFixed(1)}%
                        </span>
                    </div>
                    
                    <div class="stock-card-bottom">
                        <span class="stock-current-price">$${stock.price.toFixed(2)}</span>
                        <span class="stock-name-small">${stock.name}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function getPriceRange(symbol) {
    const prices = state.stockHistories[symbol];
    if (!prices || prices.length < 2) return null;
    
    return {
        min: Math.min(...prices),
        max: Math.max(...prices)
    };
}

function generateCardChart(symbol, isPositive) {
    const prices = state.stockHistories[symbol];
    
    // Show loading state if no data
    if (!prices || prices.length < 2) {
        const color = isPositive ? '#10b981' : '#ef4444';
        const bgColor = isPositive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
        return `
            <div class="chart-placeholder" style="background: ${bgColor}; color: ${color};">
                📊
            </div>
        `;
    }
    
    const width = 300;
    const height = 120;
    const paddingX = 0;
    const paddingTop = 30;  // Leave space at top for text
    const paddingBottom = 30;  // Leave space at bottom for text
    
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const range = maxPrice - minPrice || 1;
    
    // Generate points for the line
    const points = prices.map((price, i) => {
        const x = paddingX + (i / (prices.length - 1)) * (width - 2 * paddingX);
        const y = paddingTop + ((maxPrice - price) / range) * (height - paddingTop - paddingBottom);
        return { x, y };
    });
    
    const linePoints = points.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    
    const strokeColor = isPositive ? '#10b981' : '#ef4444';
    const gradientId = `grad-${symbol}-${Date.now()}`;
    const gradientStart = isPositive ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)';
    const gradientEnd = isPositive ? 'rgba(16, 185, 129, 0)' : 'rgba(239, 68, 68, 0)';
    
    // Create area points for filled polygon (fill to bottom)
    const firstPoint = points[0];
    const lastPoint = points[points.length - 1];
    const areaPoints = `${firstPoint.x.toFixed(1)},${height} ${linePoints} ${lastPoint.x.toFixed(1)},${height}`;
    
    return `
        <svg class="card-chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
            <defs>
                <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="${gradientStart}" />
                    <stop offset="100%" stop-color="${gradientEnd}" />
                </linearGradient>
            </defs>
            <polygon points="${areaPoints}" fill="url(#${gradientId})" />
            <polyline points="${linePoints}" fill="none" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
    `;
}

function generateSparkline(symbol, isPositive) {
    const prices = state.stockHistories[symbol];
    
    if (!prices || prices.length < 2) {
        return '<div class="sparkline-placeholder">Loading...</div>';
    }
    
    const width = 100;
    const height = 40;
    const padding = 2;
    
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const range = maxPrice - minPrice || 1;
    
    // Generate points for the sparkline
    const points = prices.map((price, i) => {
        const x = padding + (i / (prices.length - 1)) * (width - 2 * padding);
        const y = height - padding - ((price - minPrice) / range) * (height - 2 * padding);
        return `${x},${y}`;
    }).join(' ');
    
    const strokeColor = isPositive ? '#10b981' : '#ef4444';
    const fillColor = isPositive ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';
    
    // Create area fill
    const firstX = padding;
    const lastX = padding + ((prices.length - 1) / (prices.length - 1)) * (width - 2 * padding);
    const areaPoints = `${firstX},${height - padding} ${points} ${lastX},${height - padding}`;
    
    return `
        <svg class="sparkline-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
            <polygon points="${areaPoints}" fill="${fillColor}" />
            <polyline points="${points}" fill="none" stroke="${strokeColor}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
    `;
}

function renderPortfolio() {
    if (!state.portfolio) return;
    
    const cash = state.portfolio.cash_balance || 0;
    
    // Calculate total portfolio value using current prices
    let positionsValue = 0;
    state.portfolio.positions.forEach(pos => {
        const stock = state.stocks.find(s => s.symbol === pos.symbol);
        if (stock) {
            positionsValue += pos.quantity * stock.price;
        }
    });
    
    const totalValue = cash + positionsValue;
    
    elements.cashBalance.textContent = `$${cash.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    elements.positionsValue.textContent = `$${positionsValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    elements.portfolioValue.textContent = `$${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    elements.userBalance.textContent = `$${cash.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    
    // Render positions
    if (state.portfolio.positions.length === 0) {
        elements.positionsList.innerHTML = '<div class="empty-state">No positions yet<br><small>Buy some stocks to get started!</small></div>';
    } else {
        elements.positionsList.innerHTML = state.portfolio.positions.map(pos => {
            const stock = state.stocks.find(s => s.symbol === pos.symbol);
            const currentValue = stock ? pos.quantity * stock.price : pos.total_cost;
            const pnl = currentValue - (pos.quantity * pos.avg_cost);
            const pnlPct = ((currentValue / (pos.quantity * pos.avg_cost)) - 1) * 100;
            const pnlClass = pnl >= 0 ? 'text-success' : 'text-danger';
            
            return `
                <div class="position-item" onclick="openTradeModal('${pos.symbol}', 'sell')">
                    <div class="position-info">
                        <span class="position-symbol">${pos.symbol}</span>
                        <span class="position-qty">${pos.quantity} × $${pos.avg_cost.toFixed(2)}</span>
                    </div>
                    <div class="position-value">
                        <span class="${pnlClass}">$${currentValue.toFixed(2)}</span>
                        <span class="position-pnl ${pnlClass}">${pnl >= 0 ? '+' : ''}${pnlPct.toFixed(1)}%</span>
                    </div>
                </div>
            `;
        }).join('');
    }
}

function renderTrades() {
    if (state.trades.length === 0) {
        elements.tradesList.innerHTML = '<div class="empty-state">No trades yet<br><small>Execute your first trade!</small></div>';
        return;
    }
    
    // Show most recent first
    const recentTrades = [...state.trades].reverse().slice(0, 20);
    
    elements.tradesList.innerHTML = recentTrades.map(trade => {
        const time = new Date(trade.executed_at).toLocaleTimeString();
        return `
            <div class="trade-item ${trade.side}">
                <div class="trade-header">
                    <span class="trade-type">${trade.side}</span>
                    <span class="trade-time">${time}</span>
                </div>
                <div class="trade-details">
                    ${trade.symbol} × ${trade.quantity} @ $${trade.price.toFixed(2)}
                </div>
            </div>
        `;
    }).join('');
}

function renderLogs() {
    const recentLogs = state.logs.slice(0, 50);
    
    elements.logsList.innerHTML = recentLogs.map(entry => {
        const time = new Date(entry.timestamp).toLocaleTimeString();
        return `
            <div class="log-entry ${entry.level}">
                <span class="log-time">${time}</span> ${entry.message}
            </div>
        `;
    }).join('');
}

function renderMetrics(metrics) {
    const html = `
        <div class="metric-card">
            <h4>Uptime</h4>
            <div class="metric-value">${metrics.uptime_human}</div>
        </div>
        <div class="metric-card">
            <h4>Total Requests</h4>
            <div class="metric-value">${metrics.summary.total_requests.toLocaleString()}</div>
        </div>
        <div class="metric-card">
            <h4>Error Rate</h4>
            <div class="metric-value ${metrics.summary.error_rate_percent > 5 ? 'text-danger' : ''}">${metrics.summary.error_rate_percent}%</div>
            <div class="metric-subvalue">${metrics.summary.total_errors} errors</div>
        </div>
        <div class="metric-card">
            <h4>Trades Processed</h4>
            <div class="metric-value">${metrics.summary.trades_processed}</div>
            <div class="metric-subvalue">$${metrics.summary.trades_total_value.toLocaleString()} total</div>
        </div>
        <div class="metric-card">
            <h4>Emails Sent</h4>
            <div class="metric-value">${metrics.summary.emails_sent}</div>
        </div>
        <div class="metric-card">
            <h4>Auth Attempts</h4>
            <div class="metric-value">${metrics.summary.auth_attempts}</div>
            <div class="metric-subvalue">${metrics.summary.auth_failure_rate}% failure rate</div>
        </div>
        
        ${Object.entries(metrics.endpoints || {}).slice(0, 6).map(([endpoint, stats]) => `
            <div class="metric-card">
                <h4>${endpoint}</h4>
                <div class="metric-value">${stats.avg_ms.toFixed(0)}ms avg</div>
                <div class="metric-subvalue">
                    p95: ${stats.p95_ms.toFixed(0)}ms | 
                    p99: ${stats.p99_ms.toFixed(0)}ms | 
                    ${stats.count} reqs
                </div>
            </div>
        `).join('')}
    `;
    
    elements.metricsGrid.innerHTML = html;
}

function renderChart(history) {
    if (!history || history.length === 0) {
        elements.chartContainer.innerHTML = '<div class="empty-state">No history available</div>';
        return;
    }
    
    const prices = history.map(h => h.close || h.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const range = maxPrice - minPrice || 1;
    
    const width = elements.chartContainer.offsetWidth || 300;
    const height = 150;
    const padding = 5;
    
    // Determine if overall trend is positive or negative
    const startPrice = prices[0];
    const endPrice = prices[prices.length - 1];
    const isPositive = endPrice >= startPrice;
    const colorClass = isPositive ? 'positive' : 'negative';
    
    // Calculate performance
    const perfPct = ((endPrice - startPrice) / startPrice * 100).toFixed(1);
    elements.chartPerformance.textContent = `${isPositive ? '+' : ''}${perfPct}%`;
    elements.chartPerformance.className = `chart-perf ${colorClass}`;
    
    // Create path data
    const points = prices.map((price, i) => {
        const x = padding + (i / (prices.length - 1)) * (width - 2 * padding);
        const y = height - padding - ((price - minPrice) / range) * (height - 2 * padding);
        return { x, y };
    });
    
    // Create line path
    const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    
    // Create area path (closed polygon)
    const areaPath = linePath + ` L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`;
    
    // Render SVG
    elements.chartContainer.innerHTML = `
        <svg class="chart-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
            <path class="chart-area ${colorClass}" d="${areaPath}" />
            <path class="chart-line ${colorClass}" d="${linePath}" />
        </svg>
        <div class="chart-labels">
            <span>${history[0].date}</span>
            <span>${history[history.length - 1].date}</span>
        </div>
    `;
}

// ============================================
// Modal Functions
// ============================================

async function openTradeModal(symbol, type = 'buy') {
    const stock = state.stocks.find(s => s.symbol === symbol);
    if (!stock) {
        log(`Stock ${symbol} not found`, 'error');
        return;
    }
    
    state.selectedStock = stock;
    state.tradeType = type;
    
    // Update modal content
    elements.modalSymbol.textContent = stock.symbol;
    elements.modalStockName.textContent = stock.name;
    elements.modalPrice.textContent = `$${stock.price.toFixed(2)}`;
    
    // Update change display
    const changeClass = stock.daily_change >= 0 ? 'positive' : 'negative';
    const changeSign = stock.daily_change >= 0 ? '+' : '';
    elements.modalChange.textContent = `${changeSign}$${Math.abs(stock.daily_change).toFixed(2)} (${changeSign}${stock.daily_change_pct.toFixed(2)}%)`;
    elements.modalChange.className = `stock-change-display ${changeClass}`;
    
    elements.pricePerShare.textContent = `$${stock.price.toFixed(2)}`;
    elements.quantity.value = 1;
    elements.availableFunds.textContent = `$${(state.portfolio?.cash_balance || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    
    // Show shares owned if selling
    const position = state.portfolio?.positions.find(p => p.symbol === symbol);
    if (position) {
        elements.sharesOwnedRow.style.display = 'flex';
        elements.sharesOwned.textContent = position.quantity;
    } else {
        elements.sharesOwnedRow.style.display = 'none';
    }
    
    // Set trade type
    setTradeType(type);
    
    // Update estimated total
    updateEstimatedTotal();
    
    // Fetch and render chart
    elements.chartContainer.innerHTML = '<div class="loading">Loading chart...</div>';
    const history = await fetchStockHistory(symbol);
    state.selectedStockHistory = history;
    renderChart(history);
    
    // Show modal
    elements.tradeModal.classList.add('active');
}

function closeTradeModal() {
    elements.tradeModal.classList.remove('active');
    state.selectedStock = null;
    state.selectedStockHistory = null;
}

function setTradeType(type) {
    state.tradeType = type;
    
    if (type === 'buy') {
        elements.buyBtn.classList.add('active');
        elements.sellBtn.classList.remove('active');
        elements.executeTrade.classList.remove('btn-danger');
        elements.executeTrade.classList.add('btn-success');
    } else {
        elements.sellBtn.classList.add('active');
        elements.buyBtn.classList.remove('active');
        elements.executeTrade.classList.remove('btn-success');
        elements.executeTrade.classList.add('btn-danger');
    }
    
    updateExecuteButton();
}

function updateExecuteButton() {
    const type = state.tradeType;
    const icon = type === 'buy' ? '📈' : '📉';
    elements.executeTrade.innerHTML = `<span class="btn-icon">${icon}</span> Execute ${type.charAt(0).toUpperCase() + type.slice(1)} Order`;
}

function updateEstimatedTotal() {
    if (!state.selectedStock) return;
    
    const quantity = parseInt(elements.quantity.value) || 0;
    const total = quantity * state.selectedStock.price;
    
    elements.quantityDisplay.textContent = `${quantity} share${quantity !== 1 ? 's' : ''}`;
    elements.estimatedTotal.textContent = `$${total.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
}

function openBalanceModal() {
    elements.balanceModal.classList.add('active');
}

function closeBalanceModal() {
    elements.balanceModal.classList.remove('active');
}

function openMetricsModal() {
    elements.metricsModal.classList.add('active');
    fetchMetrics();
}

function closeMetricsModal() {
    elements.metricsModal.classList.remove('active');
}

// ============================================
// Event Listeners
// ============================================

function setupEventListeners() {
    // Trade modal
    document.getElementById('closeModal').addEventListener('click', closeTradeModal);
    elements.tradeModal.querySelector('.modal-backdrop').addEventListener('click', closeTradeModal);
    elements.buyBtn.addEventListener('click', () => setTradeType('buy'));
    elements.sellBtn.addEventListener('click', () => setTradeType('sell'));
    elements.quantity.addEventListener('input', updateEstimatedTotal);
    elements.executeTrade.addEventListener('click', executeTrade);
    
    // Quantity buttons
    document.getElementById('qtyMinus').addEventListener('click', () => {
        const current = parseInt(elements.quantity.value) || 1;
        if (current > 1) {
            elements.quantity.value = current - 1;
            updateEstimatedTotal();
        }
    });
    
    document.getElementById('qtyPlus').addEventListener('click', () => {
        const current = parseInt(elements.quantity.value) || 0;
        elements.quantity.value = current + 1;
        updateEstimatedTotal();
    });
    
    // Quick quantity buttons
    document.querySelectorAll('.quick-qty-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            elements.quantity.value = btn.dataset.qty;
            updateEstimatedTotal();
        });
    });
    
    // Balance modal
    document.getElementById('setBalanceBtn').addEventListener('click', openBalanceModal);
    document.getElementById('closeBalanceModal').addEventListener('click', closeBalanceModal);
    elements.balanceModal.querySelector('.modal-backdrop').addEventListener('click', closeBalanceModal);
    document.getElementById('confirmBalance').addEventListener('click', async () => {
        const amount = parseFloat(elements.newBalance.value);
        if (amount >= 0) {
            await setBalance(amount);
            closeBalanceModal();
        }
    });
    
    // Quick amount buttons
    document.querySelectorAll('.quick-amount').forEach(btn => {
        btn.addEventListener('click', () => {
            elements.newBalance.value = btn.dataset.amount;
        });
    });
    
    // Metrics modal
    document.getElementById('metricsBtn').addEventListener('click', openMetricsModal);
    document.getElementById('closeMetricsModal').addEventListener('click', closeMetricsModal);
    elements.metricsModal.querySelector('.modal-backdrop').addEventListener('click', closeMetricsModal);
    
    // Market controls
    document.getElementById('refreshMarket').addEventListener('click', async () => {
        log('Refreshing market data...', 'info');
        await fetchStocks();
    });
    document.getElementById('tickMarket').addEventListener('click', simulateMarketTick);
    
    // Activity tabs
    document.querySelectorAll('.activity-tabs .tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            
            // Update active tab
            document.querySelectorAll('.activity-tabs .tab').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            
            // Show correct content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`${tabName}Tab`).classList.add('active');
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeTradeModal();
            closeBalanceModal();
            closeMetricsModal();
        }
    });
}

// ============================================
// Initialization
// ============================================

async function init() {
    log('TradeSim initializing...', 'info');
    
    setupEventListeners();
    
    // Initial data load
    try {
        await Promise.all([
            fetchStocks(),
            fetchPortfolio(),
            fetchTradeHistory()
        ]);
        
        // Fetch historical data for mini charts
        await fetchAllStockHistories();
        
        // Set default balance if not set
        if (!state.portfolio?.cash_balance) {
            log('Setting default balance of $100,000', 'info');
            await setBalance(100000);
        }
        
        log('✓ TradeSim ready! Click any stock to trade.', 'success');
        log('📈 Market auto-updates every second', 'info');
    } catch (error) {
        log('Failed to initialize - is the backend running?', 'error');
    }
    
    // Auto-tick market prices every second
    setInterval(async () => {
        if (state.connected) {
            try {
                await apiCall('/api/market/tick', { method: 'POST' });
                await fetchStocks();
                await fetchAllStockHistories(); // Keep charts updated
                renderPortfolio(); // Update position values
            } catch (error) {
                // Silent fail for auto-tick
            }
        }
    }, CONFIG.TICK_INTERVAL);
}

// Start the app
init();

// Make functions globally available for onclick handlers
window.openTradeModal = openTradeModal;
