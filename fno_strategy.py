import pandas as pd
import ta 

def analyze_futures(df, live_price):
    if df is None or len(df) < 25:
        return None

    # Futures Indicators
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    
    # ATR for Volatility
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()

    current_rsi = df['rsi'].iloc[-1]
    ema_9 = df['ema_9'].iloc[-1]
    ema_21 = df['ema_21'].iloc[-1]
    atr = df['atr'].iloc[-1]

    signal = "NEUTRAL"
    logic = "Consolidating"
    
    # FUTURES LOGIC: EMA Crossover with RSI confirmation
    if ema_9 > ema_21 and current_rsi > 55:
        signal = "BUY TREND"
        logic = "EMA Bullish Cross"
    elif ema_9 < ema_21 and current_rsi < 45:
        signal = "SELL TREND"
        logic = "EMA Bearish Cross"

    # 🚀 NEW: Points to Capture System (ATR based)
    sl_points = atr * 1.5       # Stoploss points
    target_points = atr * 3.0   # Target points (1:2 Risk-Reward)

    return {
        "signal": signal,
        "rsi": round(current_rsi, 1),
        "logic": logic,
        "sl_points": round(sl_points, 4) if sl_points > 0 else 0,
        "target_points": round(target_points, 4) if target_points > 0 else 0
    }
