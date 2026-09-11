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
    volume_spike = False
    global_macro_safe = True # Default macro safe

    if pro_mode:
        # VWAP (Institutional Average Price)
        df['vwap'] = ta.volume.VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14).volume_weighted_average_price()
        # OBV (Smart Money Tracker)
        df['obv'] = ta.volume.OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()
        df['obv_ema'] = ta.trend.EMAIndicator(df['obv'], window=14).ema_indicator() 
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close=df["close"], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()

        # 1. Volume Spike Detector (Volume > 2.5x of average volume)
        df['vol_ma'] = df['volume'].rolling(window=20).mean()
        latest_vol = df['volume'].iloc[-1]
        avg_vol = df['vol_ma'].iloc[-1]
        if not pd.isna(avg_vol) and latest_vol > (avg_vol * 2.5):
            volume_spike = True

        # 2. Global Macro Correlation Filter (Risk-ON check via overall market movement)
        # Agar market ka average close pichle 5 candles mein gir raha hai, toh Risk-OFF maana jayega
        recent_trend = df['close'].iloc[-5:].pct_change().mean()
        if recent_trend < -0.005: # Agar sharp down move hai
            global_macro_safe = False

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
    trail_sl_points = atr * 0.8 # Dynamic Trailing SL buffer

    # ==========================================
    # 🎯 MODE 1: SNIPER MODE (Toggle ON with Pro Filters)
    # ==========================================
    if pro_mode:
        vwap = df['vwap'].iloc[-1]
        obv = df['obv'].iloc[-1]
        obv_ema = df['obv_ema'].iloc[-1]
        bb_high = df['bb_high'].iloc[-1]
        bb_low = df['bb_low'].iloc[-1]

        # Extra badge text for Volume Spike
        spike_tag = " 🔥 [VOL SPIKE]" if volume_spike else ""

        # Breakout Logic + Macro Filter Check
        if live_price > bb_high and live_price > vwap and obv > obv_ema and adx > 25:
            if global_macro_safe:
                signal = f"💥 SUPER BUY (Breakout){spike_tag}"
                logic = "Smart Money Buy + VWAP Breakout (Macro Safe)"
                score = 99
                target_points = atr * 5.0 
            else:
                signal = "⏳ SNIPER WAIT (Macro Risk-OFF)"
                logic = "Breakout detected, but Global Macro is Risk-OFF. Skipped."
                score = 65
            
        elif live_price < bb_low and live_price < vwap and obv < obv_ema and adx > 25:
            # Short signals are preferred when Macro is Risk-OFF
            signal = f"🩸 SUPER SELL (Breakout){spike_tag}"
            logic = "Smart Money Sell + VWAP Breakout (Macro Aligned)"
            score = 99
            target_points = atr * 5.0
            
        else:
            signal = "⏳ SNIPER WAIT (Accumulation)"
            logic = "Institutions Building Position (No Breakout Yet)"
            score = int(current_rsi) if not pd.isna(current_rsi) else 50

    # ==========================================
    # 🛡️ MODE 2: STANDARD MODE (Toggle OFF - Safe Logic)
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

    # Safe Entry Range buffer
    entry_buffer = atr * 0.15
    entry_min = live_price - entry_buffer
    entry_max = live_price + entry_buffer
    
    # Agar Wait signal hai, toh target/sl zero kar do taaki confusion na ho
    if "WAIT" in signal:
        sl_points = 0
        target_points = 0
        trail_sl_points = 0
        
    return {
        "signal": signal,
        "rsi": round(current_rsi, 1),
        "score": score,
        "logic": logic,
        "sl_points": round(sl_points, 4) if sl_points > 0 else 0,
        "target_points": round(target_points, 4) if target_points > 0 else 0,
        "trail_sl": round(trail_sl_points, 4) if trail_sl_points > 0 else 0,
        "entry_range": f"${round(min(entry_min, entry_max), 2)} - ${round(max(entry_min, entry_max), 2)}" if "WAIT" not in signal else "N/A"
    }
