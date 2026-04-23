import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
from datetime import datetime
from curl_cffi import requests as curl_requests

app = Flask(__name__)
CORS(app)

YF_PROXY_API_KEY = os.environ.get('YF_PROXY_API_KEY', None)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/get_stock', methods=['GET'])
def get_stock():
    if YF_PROXY_API_KEY:
        api_key = request.args.get('api_key')
        if api_key != YF_PROXY_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
    
    ticker = request.args.get('ticker', '').upper()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    interval = request.args.get('interval', '1d')
    
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    
    try:
        interval_map = {'1d': '1d', '1D': '1d', '4H': '1h', '1W': '1wk'}
        yf_interval = interval_map.get(interval, '1d')
        
        # Create a browser-impersonating session
        session = curl_requests.Session(impersonate="chrome")
        
        # Use the session with yfinance
        ticker_obj = yf.Ticker(ticker, session=session)
        df = ticker_obj.history(start=start_date, end=end_date, interval=yf_interval, auto_adjust=True)
        
        if df.empty:
            return jsonify({"error": f"No data for {ticker}"}), 404
        
        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
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
    if YF_PROXY_API_KEY:
        api_key = request.args.get('api_key')
        if api_key != YF_PROXY_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
    
    ticker = request.args.get('ticker', '').upper()
    
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400
    
    try:
        # Create a browser-impersonating session
        session = curl_requests.Session(impersonate="chrome")
        ticker_obj = yf.Ticker(ticker, session=session)
        hist = ticker_obj.history(period="1d")
        
        if hist.empty:
            return jsonify({"error": f"No price data for {ticker}"}), 404
        
        current_price = hist['Close'].iloc[-1]
        return jsonify({"ticker": ticker, "price": float(current_price)})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
