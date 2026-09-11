import streamlit as st
import time
from fno_data import get_futures_prices, get_futures_candles
from fno_strategy import analyze_futures

st.set_page_config(page_title="Global Futures AI", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }
    .buy-signal { color: #00FF00; font-weight: bold; }
    .sell-signal { color: #FF0000; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Global Futures Scanner (CoinDCX Pairs)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    timeframe = st.selectbox("TIMEFRAME", ["1h", "4h", "15m", "5m"])
with col2:
    filter_sig = st.selectbox("FILTER SIGNAL", ["All", "BUY TREND", "SELL TREND"])
with col3:
    auto_refresh = st.checkbox("Auto-Refresh (3 Min)", value=False)
with col4:
    capital = st.number_input("CAPITAL REQ (USDT)", value=1000)

if st.button("🚀 Scan Global Markets") or auto_refresh:
    with st.spinner("Analyzing Global Futures & Indices..."):
        # 1. Fetch live prices directly from updated fno_data
        live_prices = get_futures_prices()
        
        # 2. Tumhare Screenshot wale exact Global Futures pairs
        top_futures_pairs = [
            "NSDQ100", "S&P500", "SKHX", "SPCX", 
            "SNDK", "MU", "DRAM", "SKHY", "SMSN"
        ] 
        
        stocks_found = 0

        for pair in top_futures_pairs:
            # Ab humein koi loop lagakar match nahi karna, direct naam se price mil jayegi
            current_price = live_prices.get(pair, 0.0)
            
            if current_price > 0:
                stocks_found += 1
                df = get_futures_candles(pair, interval=timeframe)
                
                if df is not None and not df.empty:
                    analysis = analyze_futures(df, current_price)
                    
                    if analysis and (filter_sig == "All" or filter_sig == analysis['signal']):
                        color_hex = "#00FF00" if analysis['signal'] == "BUY TREND" else ("#FF0000" if analysis['signal'] == "SELL TREND" else "#FFA500")
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="display:flex; justify-content:space-between;">
                                <div><small style="color:gray;">GLOBAL ASSET</small><br><b>{pair}</b></div>
                                <div><small style="color:gray;">LIVE PRICE</small><br><b>${current_price}</b></div>
                                <div><small style="color:gray;">SIGNAL</small><br><span style="color:{color_hex};"><b>{analysis['signal']}</b></span></div>
                                <div><small style="color:gray;">RSI</small><br><b>{analysis['rsi']}</b></div>
                                <div><small style="color:gray;">STRATEGY</small><br><b>{analysis['logic']}</b></div>
                            </div>
                            <hr style="border-color:#333;">
                            <div style="display:flex; justify-content:space-between; font-size: 14px;">
                                <div><small style="color:gray;">TARGET:</small> <span style="color:#00FF00;">${analysis['target']}</span></div>
                                <div><small style="color:gray;">STOP-LOSS:</small> <span style="color:#FF0000;">${analysis['sl']}</span></div>
                                <div><small style="color:gray;">R:R RATIO:</small> 1:2</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        if stocks_found == 0:
            st.error("⚠️ Data fetch nahi ho paya. Ek baar check karo ki fno_data.py mein yfinance theek se chal raha hai ya nahi.")

    if auto_refresh:
        time.sleep(180) # 3 Min safe refresh
        st.rerun()
