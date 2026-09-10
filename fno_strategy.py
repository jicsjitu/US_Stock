import pandas as pd
import ta 

def analyze_futures(df, live_price):
    if df is None or len(df) < 25:
        return None

    # Futures Indicators
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['ema_9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema_21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    
    # ATR for Dynamic Stoploss (Volatility map karta hai)
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

    # Futures Target & Stop Loss Logic (Using ATR instead of fixed %)
    # Yeh aapko liquidations se bachayega
    if signal == "BUY TREND":
        sl = live_price - (atr * 1.5)       # SL 1.5x of ATR
        target = live_price + (atr * 3.0)   # Target 3x of ATR (1:2 RR)
    elif signal == "SELL TREND":
        sl = live_price + (atr * 1.5)
        target = live_price - (atr * 3.0)
    else:
        sl, target = 0, 0

    return {
        "signal": signal,
        "rsi": round(current_rsi, 1),
        "logic": logic,
        "sl": round(sl, 4) if sl > 0 else 0,
        "target": round(target, 4) if target > 0 else 0
    }
