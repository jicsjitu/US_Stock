import pandas as pd
import ta 
import numpy as np

def analyze_futures(df, live_price, pro_mode=False):
    # Minimum 50 candles chahiye EMA 50 ke liye
    if df is None or len(df) < 50:
        return None

    # ==========================================
    # 📊 STANDARD INDICATORS (Dono Mode ke liye zaroori)
    # ==========================================
    df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    
    df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
    
    macd = ta.trend.MACD(df['close'])
    df['macd_line'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()

    # ==========================================
    # 🔥 HEAVY PRO INDICATORS (Sirf Sniper Mode ke liye)
    # ==========================================
    if pro_mode:
        # VWAP (Institutional Average Price)
        df['vwap'] = ta.volume.VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14).volume_weighted_average_price()
        # OBV (Smart Money Tracker)
        df['obv'] = ta.volume.OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()
        df['obv_ema'] = ta.trend.EMAIndicator(df['obv'], window=14).ema_indicator() # OBV Trend Check
        # Bollinger Bands (For Explosive Breakout)
        bb = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()

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
    
    sl_points = atr * 1.5
    target_points = atr * 3.0

    # ==========================================
    # 🎯 MODE 1: SNIPER MODE (Toggle ON)
    # ==========================================
    if pro_mode:
        vwap = df['vwap'].iloc[-1]
        obv = df['obv'].iloc[-1]
        obv_ema = df['obv_ema'].iloc[-1]
        bb_high = df['bb_high'].iloc[-1]
        bb_low = df['bb_low'].iloc[-1]

        # Breakout Logic + Smart Money Check
        if live_price > bb_high and live_price > vwap and obv > obv_ema and adx > 25:
            signal = "💥 SUPER BUY (Breakout)"
            logic = "Smart Money Buy + VWAP Breakout"
            score = 99
            target_points = atr * 5.0 # Bada target for breakout
            
        elif live_price < bb_low and live_price < vwap and obv < obv_ema and adx > 25:
            signal = "🩸 SUPER SELL (Breakout)"
            logic = "Smart Money Sell + VWAP Breakout"
            score = 99
            target_points = atr * 5.0
            
        else:
            signal = "⏳ SNIPER WAIT (Accumulation)"
            logic = "Institutions Building Position (No Breakout Yet)"
            score = int(current_rsi) if not pd.isna(current_rsi) else 50

    # ==========================================
    # 🛡️ MODE 2: STANDARD MODE (Toggle OFF - Tumhara Purana Safe Logic)
    # ==========================================
    else:
        if adx < 20:
            signal = "⏳ WAIT (Sideways)"
            logic = "Low Volatility (ADX < 20)"
            score = int(current_rsi) if not pd.isna(current_rsi) else 30
        else:
            if ema_9 > ema_21 and macd_l > macd_s:
                if live_price > ema_50:
                    signal = "🚀 BUY TREND"
                    logic = "Strong Uptrend + Momentum"
                    score = min(95, int(60 + adx)) 
                else:
                    signal = "⚠️ WEAK BUY"
                    logic = "Pullback (Against Trend)"
                    score = 55
                    
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
