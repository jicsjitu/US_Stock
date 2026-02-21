import pandas as pd
import numpy as np
import yfinance as yf
import time

# ==========================================
# 🇺🇸 US STOCKS CONFIGURATION (CoinDCX USDC Pairs)
# ==========================================
# Left: Yahoo Finance Ticker | Right: CoinDCX Display Name
US_PAIRS = {
    'NQ=F': 'NSDQ100/USDC', # Nasdaq 100 Futures
    'NVDA': 'NVDA/USDC',    # Nvidia
    'WDC': 'SNDK/USDC',     # Sandisk (Acquired by Western Digital)
    'TSLA': 'TSLA/USDC',    # Tesla
    'MU': 'MU/USDC',        # Micron Technology
    'PLTR': 'PLTR/USDC',    # Palantir Technologies
    'GOOGL': 'GOOGL/USDC',  # Alphabet (Google)
    'MSTR': 'MSTR/USDC',    # MicroStrategy
    'COIN': 'COIN/USDC',    # Coinbase
    'INTC': 'INTC/USDC',    # Intel
    'HOOD': 'HOOD/USDC',    # Robinhood
    'AAPL': 'AAPL/USDC',    # Apple
    'AMD': 'AMD/USDC',      # AMD
    'MSFT': 'MSFT/USDC',    # Microsoft
    'ORCL': 'ORCL/USDC',    # Oracle
    'AMZN': 'AMZN/USDC',    # Amazon
    'NFLX': 'NFLX/USDC',    # Netflix
    'BABA': 'BABA/USDC',    # Alibaba
    'CRCL': 'CRCL/USDC',    # CoreCard / Circle proxy
    'META': 'META/USDC'     # Meta (Facebook)
}

TIMEFRAME = '5m' # 5 Minute Candles

def fetch_us_candles(ticker):
    try:
        # Fetching last 5 days data, 5 min intervals
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="5d", interval=TIMEFRAME)
        
        if df.empty or len(df) < 30:
            return None
            
        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]
        
        # Standardize datetime column
        if 'datetime' in df.columns:
            df.rename(columns={'datetime': 'timestamp'}, inplace=True)
        elif 'date' in df.columns:
            df.rename(columns={'date': 'timestamp'}, inplace=True)
            
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        return df
    except Exception as e:
        return None

def calculate_adx(df, period=14):
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / atr)
    minus_di = 100 * (abs(minus_dm).ewm(alpha=1/period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()
    return adx

def analyze_us_stock(df, dcx_pair):
    if df is None: return None
    
    # 1. Trend (EMA 50)
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # 2. Momentum (RSI)
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)
    
    # 3. Volatility (ATR)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift())
    df['tr3'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()

    # 4. Strength & Volume
    df['adx'] = calculate_adx(df)
    df['vol_ma'] = df['volume'].rolling(20).mean()
    
    curr = df.iloc[-1]
    
    price = curr['close']
    ema = curr['ema_50']
    rsi = curr['rsi']
    atr = curr['atr'] if curr['atr'] > 0 else price * 0.01
    adx = curr['adx']
    vol = curr['volume']
    vol_avg = curr['vol_ma']
    
    is_green_candle = curr['close'] > curr['open']
    
    # --- 1% TRADER LOGIC (Tailored for US Stocks) ---
    signal = "WAIT ⏳"
    reason = "No Setup"
    score = 0
    target = 0
    stop_loss = 0
    
    if price > ema:
        score += 10
        reason = "Uptrend (Waiting for Volume)"
    
    has_volume = vol > vol_avg
    if has_volume: score += 10
        
    # STRATEGY 1: Tech Momentum Breakout
    if price > ema and 50 < rsi < 75 and adx > 18 and is_green_candle and has_volume:
        score += 60
        signal = "BUY TREND 🚀"
        reason = f"Strong Wall St Rally (ADX {adx:.0f})"
        
    # STRATEGY 2: Dip Buying
    elif rsi < 35 and is_green_candle: 
        score += 50
        signal = "BUY DIP 🟢"
        reason = "Oversold + Institutional Buying"
        
    # STRATEGY 3: Profit Booking
    elif rsi > 80:
        score -= 20
        signal = "SELL 🔴"
        reason = "Overbought (Risk High)"
    
    # Filter out weak fake moves
    if adx < 15 and "BUY" in signal:
        signal = "WAIT ⏳"
        reason = "Weak Trend (Avoid Trap)"
        score = 20
        
    # Strict US Market Risk Management (1:2 Risk-Reward)
    if "BUY" in signal:
        stop_loss = price - (1.5 * atr) 
        target = price + (3.0 * atr)    
        
    return {
        "pair": dcx_pair,
        "price": price,
        "signal": signal,
        "score": score,
        "reason": reason,
        "target": target,
        "stop_loss": stop_loss,
        "atr": atr,
        "rsi": rsi,
        "adx": adx
    }

def run_us_agent():
    # Base Capital: $1000 USDC Virtual
    balance = 1000.00 
    results = []
    
    for yf_ticker, dcx_pair in US_PAIRS.items():
        df = fetch_us_candles(yf_ticker)
        if df is not None:
            analysis = analyze_us_stock(df, dcx_pair)
            if analysis:
                results.append(analysis)
        time.sleep(0.1) # Safe delay for Yahoo Finance
        
    return results, balance