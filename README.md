# TradeSim - Trading Platform Demo

A demonstration trading platform built to showcase the challenges of monitoring and debugging applications **without proper observability tooling**.

![TradeSim Screenshot](docs/screenshot.png)

## 🎯 Purpose

This application is designed for Datadog sales demonstrations to help customers understand:

1. **The pain of manual observability** - See how teams typically monitor systems without APM tools
2. **Hidden complexity** - Multiple services (auth, trading, email, etc.) that are hard to trace
3. **Manual logging overhead** - Every timing measurement, error log, and metric is manually coded
4. **The case for Datadog** - After seeing the manual approach, Datadog's value becomes clear

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (JS)                          │
│  - Trading Dashboard                                        │
│  - Portfolio Management                                     │
│  - Manual Activity Logging                                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (Python)                    │
├─────────────────────────────────────────────────────────────┤
│  Services:                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Auth      │ │   Trade     │ │   Fund      │           │
│  │   Service   │ │   Service   │ │   Service   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Email     │ │   Market    │ │  Portfolio  │           │
│  │   Service   │ │   Service   │ │   Service   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
├─────────────────────────────────────────────────────────────┤
│  Manual Observability:                                       │
│  - Custom logging with timing                                │
│  - Request correlation IDs                                   │
│  - Manual metrics collection                                 │
│  - Health check endpoints                                    │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Stocks

The platform includes 12 stocks with intentional performance biases:

| Symbol | Company | Behavior |
|--------|---------|----------|
| **DDOG** | Datadog, Inc. | 🚀 Strong performer, steady growth |
| SPLK | Splunk Inc. | 📉 Poor performance (competitor) |
| DT | Dynatrace, Inc. | 📉 Declining (competitor) |
| NEWR | New Relic, Inc. | 📉 Volatile, trending down (competitor) |
| ESTC | Elastic N.V. | 📉 Underperforming (competitor) |
| AAPL | Apple Inc. | Stable |
| MSFT | Microsoft | Stable/Growing |
| GOOGL | Alphabet | Stable |
| AMZN | Amazon | Stable |
| TSLA | Tesla | High volatility |
| NVDA | NVIDIA | Growing (AI boom) |
| META | Meta Platforms | Stable |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js (optional, for serving frontend)
- Modern web browser

### Backend Setup

```bash
# Navigate to project directory
cd DD-Project-App

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
cd backend
python app.py
```

The backend will start at `http://localhost:5000`

### Frontend Setup

The frontend is pure HTML/CSS/JS and can be served in multiple ways:

**Option 1: Python's built-in server**
```bash
cd frontend
python -m http.server 8080
```

**Option 2: Open directly**
Just open `frontend/index.html` in your browser (some features may be limited due to CORS)

**Option 3: VS Code Live Server**
Use the Live Server extension if you have VS Code

The frontend will be available at `http://localhost:8080`

## 🔍 Demo Walkthrough

### 1. Initial Setup
- Open the frontend in your browser
- Click "Set Balance" and add $100,000
- Note the system logs appearing in the Activity panel

### 2. Execute Trades
- Click on any stock card to trade
- Buy some DDOG (it performs well!)
- Try buying competitors and watch them decline
- Notice the manual logging in the System Logs tab

### 3. View Manual Metrics
- Click the "📊 Metrics" button in the header
- See how teams manually track:
  - Request counts and latencies
  - Error rates
  - Business metrics (trades, emails)
  - Per-endpoint performance

### 4. Simulate Issues
- Use the "⚡ Simulate Tick" button to move the market
- Try the debug endpoints to see error handling:
  ```bash
  # Slow endpoint
  curl http://localhost:5000/api/debug/slow
  
  # Error endpoint
  curl http://localhost:5000/api/debug/error?type=db
  ```

### 5. Discuss Pain Points

Use these talking points:

1. **"How do you debug a slow trade?"**
   - Manual correlation IDs
   - Grep through logs
   - No trace visualization

2. **"What if email delivery fails?"**
   - Check each service log separately
   - No unified view
   - Manual alerting

3. **"How do you know something is wrong?"**
   - Poll /health endpoints
   - Check /metrics manually
   - No automatic anomaly detection

## 📁 Project Structure

```
DD-Project-App/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── services/
│   │   ├── auth_service.py    # User authentication
│   │   ├── trade_service.py   # Trade execution
│   │   ├── fund_service.py    # Fund verification & bank transfers
│   │   ├── email_service.py   # Email notifications
│   │   ├── market_service.py  # Stock prices & market data
│   │   └── portfolio_service.py # Portfolio management
│   └── observability/
│       ├── logger.py          # Manual logging implementation
│       └── metrics.py         # Manual metrics collection
├── frontend/
│   ├── index.html             # Main HTML file
│   ├── styles.css             # Styling
│   └── app.js                 # Frontend logic
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔌 API Endpoints

### Health & Metrics
- `GET /health` - Service health check
- `GET /metrics` - Manual metrics endpoint
- `POST /metrics/reset` - Reset metrics (for demos)

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/validate` - Validate session

### Portfolio
- `GET /api/portfolio/<user_id>` - Get portfolio
- `POST /api/portfolio/<user_id>/balance` - Set balance

### Market Data
- `GET /api/market/stocks` - Get all stocks
- `GET /api/market/stocks/<symbol>` - Get specific stock
- `GET /api/market/stocks/<symbol>/history` - Get price history
- `POST /api/market/tick` - Simulate market movement

### Trading
- `POST /api/trade/buy` - Execute buy order
- `POST /api/trade/sell` - Execute sell order
- `GET /api/trade/history/<user_id>` - Get trade history

### Debug
- `GET /api/debug/slow` - Simulate slow response
- `GET /api/debug/error` - Simulate errors
- `GET /api/debug/logs` - Get recent logs

## 💡 Key Demo Points

### What This App Does Manually:

1. **Request Tracing**
   - Generates correlation IDs per request
   - Logs request/response with timing
   - No visualization or automatic correlation

2. **Metrics Collection**
   - Counts requests per endpoint
   - Calculates latency percentiles
   - Tracks error rates
   - No automatic dashboards

3. **Service Health**
   - Each service has health_check()
   - Manual polling required
   - No automatic alerting

4. **Error Handling**
   - Custom error logging
   - Error IDs for support
   - Manual log searching required

### What Datadog Would Provide:

- **APM**: Automatic distributed tracing
- **Infrastructure**: Host/container monitoring
- **Logs**: Centralized log management
- **Dashboards**: Out-of-the-box visualizations
- **Alerts**: Automatic anomaly detection
- **RUM**: Real user monitoring
- **Synthetics**: API/browser testing

## 🎨 Customization

### Adding New Stocks
Edit `backend/services/market_service.py` and add to the `STOCKS` dictionary.

### Adjusting Stock Performance
Modify the `trend` and `volatility` values in the stock configuration.

### Changing Demo User
Update `CONFIG.USER_ID` in `frontend/app.js`.

## 📝 License

This is a demo application for Datadog sales purposes.

---

**Built with ❤️ for the Datadog Sales Team**

