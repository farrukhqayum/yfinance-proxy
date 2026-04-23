import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

YF_PROXY_API_KEY = os.environ.get('YF_PROXY_API_KEY', None)

@app.route('/get_stock', methods=['GET'])
def get_stock():
    # Check API key if set
    if PROXY_API_KEY:
        api_key = request.args.get('api_key')
        if api_key != YF_PROXY_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
            
app = Flask(__name__)
CORS(app)  # Allow Streamlit app to call this proxy

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/get_stock', methods=['GET'])
def get_stock():
    """Proxy endpoint for yfinance data"""
    ticker = request.args.get('ticker', '').upper()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    interval = request.args.get('interval', '1d')
    
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    
    try:
        # Map interval for yfinance
        interval_map = {'1d': '1d', '1D': '1d', '4H': '1h', '1W': '1wk'}
        yf_interval = interval_map.get(interval, '1d')
        
        # Download data
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval=yf_interval,
            progress=False,
            auto_adjust=True,
            threads=False
        )
        
        if df.empty:
            return jsonify({"error": f"No data for {ticker}"}), 404
        
        # Convert to JSON-friendly format
        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Handle multi-index columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        result = {
            "ticker": ticker,
            "data": df.to_dict(orient='records'),
            "columns": list(df.columns)
        }
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_current_price', methods=['GET'])
def get_current_price():
    """Get current price for a ticker"""
    ticker = request.args.get('ticker', '').upper()
    
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period="1d")
        
        if hist.empty:
            return jsonify({"error": f"No price data for {ticker}"}), 404
        
        current_price = hist['Close'].iloc[-1]
        return jsonify({"ticker": ticker, "price": float(current_price)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
