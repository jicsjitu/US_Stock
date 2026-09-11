import requests
import pandas as pd
import hmac
import hashlib
import json
import time
import streamlit as st

# Streamlit secrets se API aur Secret Key fetch karna
try:
    API_KEY = st.secrets["COINDCX_API_KEY"]
    SECRET_KEY = st.secrets["COINDCX_SECRET_KEY"]
except Exception as e:
    st.error("API Keys Streamlit Secrets mein nahi mili! Kripya check karein.")
    API_KEY = ""
    SECRET_KEY = ""

TICKER_URL = "https://api.coindcx.com/exchange/ticker"
CANDLE_URL = "https://public.coindcx.com/market_data/candles"

def get_auth_headers(body=None):
    """CoinDCX ki security ke liye HMAC Signature generate karta hai"""
    if body is None:
        body = {}
    
    # Timestamp in milliseconds
    time_stamp = int(round(time.time() * 1000))
    body["timestamp"] = time_stamp
    
    json_body = json.dumps(body, separators=(',', ':'))
    
    # Signature create karna
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'), 
        json_body.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature
    }
    return headers

def get_futures_prices():
    """CoinDCX se saare live prices fetch karega (Bina B- filter ke)"""
    try:
        # Ticker ke liye normal public request kaafi hai
        response = requests.get(TICKER_URL)
        data = response.json()
        
        prices = {}
        for item in data:
            # Ab hum saare pairs ka data save kar lenge
            prices[item['market']] = float(item['last_price'])
                
        return prices
    except Exception as e:
        print(f"Price Fetch Error: {e}")
        return {}
        
def get_futures_candles(pair, interval="1h", limit=100):
    """Futures coins ka chart data layega"""
    params = {
        "pair": pair, 
        "interval": interval,
        "limit": limit
    }
    try:
        response = requests.get(CANDLE_URL, params=params)
        data = response.json()
        
        if not data or isinstance(data, dict): 
            # Fallback: Agar futures pair ka chart error de, toh spot chart use karein
            spot_pair = pair.replace("B-", "") 
            params["pair"] = spot_pair
            response = requests.get(CANDLE_URL, params=params)
            data = response.json()

        if not data or not isinstance(data, list):
            return None
            
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        # Data ko seedha karna (oldest to newest)
        df = df.iloc[::-1].reset_index(drop=True) 
        return df
    except Exception as e:
        print(f"Candle Fetch Error for {pair}: {e}")
        return None
