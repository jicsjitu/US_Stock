import streamlit as st
import time
from fno_data import get_futures_prices, get_futures_candles
from fno_strategy import analyze_futures

st.set_page_config(page_title="Global Futures AI", layout="wide", initial_sidebar_state="collapsed")

# 🧠 STREAMLIT MEMORY: Data ko gayab hone se bachane ke liye
if "scanned_results" not in st.session_state:
    st.session_state.scanned_results = None

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
    .calc-box { background-color: #2b2b2b; padding: 10px; border-radius: 5px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Global Futures Scanner (CoinDCX Sync)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    timeframe = st.selectbox("TIMEFRAME", ["1h", "4h", "15m", "5m"])
with col2:
    filter_sig = st.selectbox("FILTER SIGNAL", ["All", "BUY TREND", "SELL TREND"])
with col3:
    auto_refresh = st.checkbox("Auto-Refresh (3 Min)", value=False)
with col4:
    capital = st.number_input("CAPITAL REQ (USDT)", value=1000, step=100)

# STEP 1: Sirf tab data fetch karo jab Button dabaya jaye ya Auto-Refresh On ho
if st.button("🚀 Scan Global Markets") or auto_refresh:
    with st.spinner("Analyzing Global Futures & Indices..."):
        live_prices = get_futures_prices()
        top_futures_pairs = ["NSDQ100", "S&P500", "SKHX", "SPCX", "SNDK", "MU", "DRAM", "SKHY", "SMSN"] 
        
        results = [] # Ek khali dabbi banayi data save karne ke liye
        
        for pair in top_futures_pairs:
            current_price = live_prices.get(pair, 0.0)
            if current_price > 0:
                df = get_futures_candles(pair, interval=timeframe)
                if df is not None and not df.empty:
                    analysis = analyze_futures(df, current_price)
                    if analysis:
                        # 🧠 Data ko dabbi mein daal do
                        results.append({
                            "pair": pair,
                            "current_price": current_price,
                            "analysis": analysis
                        })
        
        # 🧠 Dabbi ko Streamlit ki Memory mein daal diya
        st.session_state.scanned_results = results


# STEP 2: UI aur Calculator Render karna (Memory se data padh ke)
if st.session_state.scanned_results is not None:
    stocks_found = 0
    
    for item in st.session_state.scanned_results:
        pair = item["pair"]
        current_price = item["current_price"]
        analysis = item["analysis"]
        
        # Filter Logic (Buy/Sell)
        if filter_sig == "All" or filter_sig == analysis['signal']:
            stocks_found += 1
            color_hex = "#00FF00" if analysis['signal'] == "BUY TREND" else ("#FF0000" if analysis['signal'] == "SELL TREND" else "#FFA500")
            
            # Position Sizing Logic (2% Risk Rule)
            risk_amount = capital * 0.02 
            safe_quantity = 0
            if analysis['sl_points'] > 0:
                safe_quantity = round(risk_amount / analysis['sl_points'], 4)

            # UI Cards Rendering
            st.markdown(f"""
            <div class="metric-card">
                <div style="display:flex; justify-content:space-between;">
                    <div><small style="color:gray;">GLOBAL ASSET</small><br><b>{pair}</b></div>
                    <div><small style="color:gray;">YAHOO PRICE</small><br><b>${current_price}</b></div>
                    <div><small style="color:gray;">SIGNAL</small><br><span style="color:{color_hex};"><b>{analysis['signal']}</b></span></div>
                    <div><small style="color:gray;">RSI</small><br><b>{analysis['rsi']}</b></div>
                    <div><small style="color:gray;">STRATEGY</small><br><b>{analysis['logic']}</b></div>
                </div>
                <hr style="border-color:#333;">
                <div style="display:flex; justify-content:space-between; font-size: 14px;">
                    <div><small style="color:gray;">TARGET MOVEMENT:</small> <span style="color:#00FF00;"><b>+{analysis['target_points']} Pts</b></span></div>
                    <div><small style="color:gray;">STOP-LOSS MOVEMENT:</small> <span style="color:#FF0000;"><b>-{analysis['sl_points']} Pts</b></span></div>
                    <div><small style="color:gray;">SAFE QUANTITY (2% Risk):</small> <b style="color:#FFD700;">{safe_quantity} Units</b></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 🧮 Magic Calculator (Ab gayab nahi hoga)
            if analysis['signal'] in ["BUY TREND", "SELL TREND"]:
                with st.expander(f"🧮 Calculator: Sync exact levels for {pair} on CoinDCX"):
                    st.markdown("<div class='calc-box'>", unsafe_allow_html=True)
                    
                    cdcx_input = st.number_input(f"Enter current {pair} price from CoinDCX App:", value=float(current_price), format="%.2f", key=f"calc_{pair}")
                    
                    if analysis['signal'] == "BUY TREND":
                        exact_target = cdcx_input + analysis['target_points']
                        exact_sl = cdcx_input - analysis['sl_points']
                        st.success(f"📈 **COINDCX LONG ENTRY SETTINGS:**\n\nTarget Price: **${round(exact_target, 2)}** | Stop-Loss Price: **${round(exact_sl, 2)}**")
                    
                    elif analysis['signal'] == "SELL TREND":
                        exact_target = cdcx_input - analysis['target_points']
                        exact_sl = cdcx_input + analysis['sl_points']
                        st.error(f"📉 **COINDCX SHORT ENTRY SETTINGS:**\n\nTarget Price: **${round(exact_target, 2)}** | Stop-Loss Price: **${round(exact_sl, 2)}**")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
    
    if stocks_found == 0:
        st.warning("⚠️ Koi trade current filter match nahi kar raha hai.")

    # Auto Refresh Logic
    if auto_refresh:
        time.sleep(180) # 3 Min safe refresh
        st.rerun()
