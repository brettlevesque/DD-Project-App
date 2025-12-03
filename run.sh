#!/bin/bash

# TradeSim - Quick Start Script
# =============================

echo "🚀 TradeSim - Trading Platform Demo"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend && python app.py"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend && python -m http.server 8080"
echo ""
echo "Then open http://localhost:8080 in your browser"
echo ""

# Ask if user wants to start backend
read -p "Start the backend server now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd backend
    python app.py
fi

