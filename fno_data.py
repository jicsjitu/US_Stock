import yfinance as yf
import pandas as pd

# CoinDCX ke naam ko Yahoo Finance ke original tickers se map kiya hai
TICKER_MAP = {
    "NSDQ100": "NQ=F",     # Nasdaq 100 Futures
    "S&P500": "ES=F",      # S&P 500 Futures
    "MU": "MU",            # Micron Technology
    "SKHX": "000660.KS",   # SK Hynix (Korean Market)
    "SKHY": "000660.KS",   
    "SMSN": "005930.KS",   # Samsung Electronics
    "SPCX": "SPY",         # S&P Proxy
    "SNDK": "WDC",         # SanDisk (Ab Western Digital ban chuka hai)
    "DRAM": "MU"           # DRAM proxy
}

def get_futures_prices():
    """Yahoo Finance se live prices fetch karega"""
    prices = {}
    for cd_name, yf_ticker in TICKER_MAP.items():
        try:
            ticker = yf.Ticker(yf_ticker)
            # Fetch last available price
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                prices[cd_name] = round(hist['Close'].iloc[-1], 2)
        except Exception as e:
            prices[cd_name] = 0.0
    return prices

def get_futures_candles(pair, interval="1h", limit=100):
    """Yahoo Finance se chart/candle data layega"""
    yf_ticker = TICKER_MAP.get(pair)
    if not yf_ticker:
        return None
    
    # yfinance intervals format: 1m, 5m, 15m, 30m, 1h, 1d
    yf_interval = interval
    if interval == "4h": 
        yf_interval = "1d" # Yahoo finance mein 4h stable nahi hota, isliye 1d
        
    try:
        ticker = yf.Ticker(yf_ticker)
        # Data fetch karna
        df = ticker.history(period="20d", interval=yf_interval)
        
        if df.empty:
            return None
            
        df = df.reset_index()
        # Humare purane logic se match karne ke liye columns ka naam chhota kar rahe hain
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        
        return df
    except Exception as e:
        print(f"Candle Fetch Error for {pair}: {e}")
        return None
