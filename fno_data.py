import requests
import pandas as pd

TICKER_URL = "https://api.coindcx.com/exchange/ticker"
CANDLE_URL = "https://public.coindcx.com/market_data/candles"

def get_futures_prices():
    """Sirf CoinDCX USDT Futures coins ke live prices fetch karega"""
    try:
        response = requests.get(TICKER_URL)
        data = response.json()
        
        # CoinDCX mein futures pairs 'B-' se shuru hote hain (e.g., B-BTC_USDT)
        prices = {}
        for item in data:
            if item['market'].startswith('B-') and 'USDT' in item['market']:
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
        
        if not data or isinstance(data, dict): # Check if error response
            # Fallback: Agar futures pair ka chart error de, toh spot chart use karein analysis ke liye
            spot_pair = pair.replace("B-", "") # 'B-BTC_USDT' -> 'BTC_USDT'
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
