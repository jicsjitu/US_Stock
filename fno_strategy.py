import pandas as pd
import ta 
import numpy as np

def analyze_futures(df, live_price):
    # Minimum 50 candles chahiye EMA 50 ke liye
    if df is None or len(df) < 50:
        return None

    # 1. Trend & Momentum (EMAs)
    df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    
    # 2. Sideways / Chop Zone Detector (ADX)
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
    
    # 3. Volume & Momentum Confirmation (MACD)
    macd = ta.trend.MACD(df['close'])
    df['macd_line'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    
    # 4. Volatility (ATR) & Overbought/Oversold (RSI)
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()

    # Get latest values
    current_rsi = df['rsi'].iloc[-1]
    ema_9 = df['ema_9'].iloc[-1]
    ema_21 = df['ema_21'].iloc[-1]
    ema_50 = df['ema_50'].iloc[-1]
    adx = df['adx'].iloc[-1]
    macd_l = df['macd_line'].iloc[-1]
    macd_s = df['macd_signal'].iloc[-1]
    atr = df['atr'].iloc[-1]

    signal = "⏳ WAIT (Sideways)"
    logic = "Consolidating"
    score = 10

    # 🚀 4-LAYER PRO LOGIC EVALUATION
    if adx < 20:
        # Strict Sideways Filter: Agar market range mein hai toh no trade!
        signal = "⏳ WAIT (Sideways)"
        logic = "Low Volatility (ADX < 20)"
        score = int(current_rsi) if not pd.isna(current_rsi) else 30
    else:
        # Bullish Check
        if ema_9 > ema_21 and macd_l > macd_s:
            if live_price > ema_50:
                signal = "🚀 BUY TREND"
                logic = "Strong Uptrend + Momentum"
                score = min(95, int(60 + adx)) # High ADX = Stronger Score
            else:
                signal = "⚠️ WEAK BUY"
                logic = "Pullback (Against Trend)"
                score = 55
                
        # Bearish Check
        elif ema_9 < ema_21 and macd_l < macd_s:
            if live_price < ema_50:
                signal = "🩸 SELL TREND"
                logic = "Strong Downtrend + Momentum"
                score = min(95, int(60 + adx))
            else:
                signal = "⚠️ WEAK SELL"
                logic = "Short Buildup (Against Trend)"
                score = 55
        else:
            signal = "⏳ WAIT (Sideways)"
            logic = "Mixed Indicators (Chop Zone)"
            score = 40

    # Dynamic Points & Entry Range (ATR Based)
    sl_points = atr * 1.5
    target_points = atr * 3.0
    
    # Safe Entry Range (live price ke aas paas ka buffer)
    entry_buffer = atr * 0.15
    entry_min = live_price - entry_buffer
    entry_max = live_price + entry_buffer

    return {
        "signal": signal,
        "rsi": round(current_rsi, 1),
        "score": score,
        "logic": logic,
        "sl_points": round(sl_points, 4) if sl_points > 0 else 0,
        "target_points": round(target_points, 4) if target_points > 0 else 0,
        "entry_range": f"${round(min(entry_min, entry_max), 2)} - ${round(max(entry_min, entry_max), 2)}"
    }
