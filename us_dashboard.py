import streamlit as st
import time
import streamlit.components.v1 as components
from fno_data import get_futures_prices, get_futures_candles
from fno_strategy import analyze_futures

st.set_page_config(page_title="Pro Algo Desk", layout="wide", initial_sidebar_state="collapsed")

# 🧠 STREAMLIT MEMORY
if "scanned_results" not in st.session_state:
    st.session_state.scanned_results = None

# Custom CSS matching exactly your screenshots
st.markdown("""
<style>
    .metric-card {
        background-color: #1a1a1c;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #2d2d30;
    }
    .card-buy { border-left: 4px solid #00e676; }
    .card-sell { border-left: 4px solid #ff1744; }
    .card-wait { border-left: 4px solid #ffb300; }
    .calc-box { background-color: #2b2b2b; padding: 10px; border-radius: 5px; margin-top: 10px; }
    .col-header { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px;}
    .col-val { color: #fff; font-size: 14px; font-weight: bold; }
    .divider { border-top: 1px solid #2d2d30; margin: 15px 0; }
</style>
""", unsafe_allow_html=True)

# Top Bar Filters (Clean & Compact)
col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1.5, 2])
with col1: timeframe = st.selectbox("TIMEFRAME", ["1h", "4h", "15m", "5m"])
with col2: filter_sig = st.selectbox("FILTER SIGNAL", ["All", "BUY", "SELL", "WAIT"])
with col3: capital = st.number_input("CAPITAL (USDT)", value=1000, step=100)
with col4: auto_refresh = st.checkbox("✅ Auto-Refresh (3 Min)", value=True)
with col5: scan_btn = st.button("🚀 Scan Markets")

# ⏳ TIMER SCRIPT (Middle / Right aligned)
if auto_refresh:
    components.html(
        """
        <div style="text-align: right; color: #ffb300; font-family: sans-serif; font-size: 15px; font-weight: bold; padding-right: 20px;">
            ⏳ Next Scan in: <span id="time" style="color:#fff;">03:00</span>
        </div>
        <script>
            var time = 180;
            setInterval(function() {
                time--;
                if(time >= 0) {
                    var m = Math.floor(time / 60);
                    var s = time % 60;
                    document.getElementById('time').innerHTML = "0" + m + ":" + (s < 10 ? "0" : "") + s;
                } else {
                    window.parent.location.reload(); 
                }
            }, 1000);
        </script>
        """,
        height=30
    )
st.write("") # Spacer

# STEP 1: Fetch Logic
if scan_btn or st.session_state.scanned_results is None:
    with st.spinner("Running 4-Layer Backend Analysis..."):
        live_prices = get_futures_prices()
        top_futures_pairs = ["NSDQ100", "S&P500", "SKHX", "SPCX", "SNDK", "MU", "DRAM", "SKHY", "SMSN"] 
        
        results = [] 
        for pair in top_futures_pairs:
            current_price = live_prices.get(pair, 0.0)
            if current_price > 0:
                # Fetch slightly more data for EMA 50 to work properly
                df = get_futures_candles(pair, interval=timeframe, limit=150) 
                if df is not None and not df.empty:
                    analysis = analyze_futures(df, current_price)
                    if analysis:
                        results.append({"pair": pair, "current_price": current_price, "analysis": analysis})
        
        st.session_state.scanned_results = results

# STEP 2: Render Screenshot-Style UI
if st.session_state.scanned_results is not None:
    stocks_found = 0
    
    for item in st.session_state.scanned_results:
        pair = item["pair"]
        current_price = item["current_price"]
        analysis = item["analysis"]
        
        # Determine styling and filtering
        sig_str = analysis['signal']
        if filter_sig != "All" and filter_sig not in sig_str:
            continue
            
        stocks_found += 1
        
        if "BUY" in sig_str: 
            card_class = "card-buy"
            color_hex = "#00e676"
        elif "SELL" in sig_str: 
            card_class = "card-sell"
            color_hex = "#ff1744"
        else: 
            card_class = "card-wait"
            color_hex = "#ffb300"
            
        risk_amount = capital * 0.02 
        safe_quantity = round(risk_amount / analysis['sl_points'], 4) if analysis['sl_points'] > 0 else 0

        # Rendering Card (HTML BUG FIXED: Removed empty lines so Streamlit doesn't break)
        st.markdown(f"""
        <div class="metric-card {card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="width:15%;"><div class="col-header">PAIR</div><div class="col-val" style="color:#ffb300;">{pair}</div></div>
                <div style="width:15%;"><div class="col-header">YAHOO PRICE</div><div class="col-val">${current_price} ➔</div></div>
                <div style="width:20%;"><div class="col-header">SIGNAL</div><div class="col-val" style="color:{color_hex};">{analysis['signal']}</div></div>
                <div style="width:10%;"><div class="col-header">RSI</div><div class="col-val">{analysis['rsi']}</div></div>
                <div style="width:10%;"><div class="col-header">SCORE</div><div class="col-val">{analysis['score']}</div></div>
                <div style="width:25%;"><div class="col-header">ANALYSIS REASON</div><div class="col-val" style="color:#aaa; font-weight:normal;">{analysis['logic']}</div></div>
            </div>
            <div class="divider"></div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="width:25%;"><div class="col-header">ENTRY RANGE</div><div class="col-val" style="font-size:12px; color:#888;">{analysis['entry_range']}</div></div>
                <div style="width:20%;"><div class="col-header">TARGET MOVEMENT</div><div class="col-val" style="color:#00e676;">+{analysis['target_points']} Pts</div></div>
                <div style="width:20%;"><div class="col-header">SL MOVEMENT</div><div class="col-val" style="color:#ff1744;">-{analysis['sl_points']} Pts</div></div>
                <div style="width:20%;"><div class="col-header">SAFE QTY (2% RISK)</div><div class="col-val">{safe_quantity} Units</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 🧮 CoinDCX Sync Calculator (BUG FIXED: Always visible now)
        with st.expander(f"🧮 Calculator: Sync exact levels for {pair} on CoinDCX"):
            st.markdown("<div class='calc-box'>", unsafe_allow_html=True)
            
            cdcx_input = st.number_input(f"Enter current {pair} price from CoinDCX App:", value=float(current_price), format="%.2f", key=f"calc_{pair}")
            
            if "BUY" in analysis['signal']:
                exact_target = cdcx_input + analysis['target_points']
                exact_sl = cdcx_input - analysis['sl_points']
                st.success(f"📈 **COINDCX LONG ENTRY SETTINGS:**\n\nTarget Price: **${round(exact_target, 2)}** | Stop-Loss Price: **${round(exact_sl, 2)}**")
            
            elif "SELL" in analysis['signal']:
                exact_target = cdcx_input - analysis['target_points']
                exact_sl = cdcx_input + analysis['sl_points']
                st.error(f"📉 **COINDCX SHORT ENTRY SETTINGS:**\n\nTarget Price: **${round(exact_target, 2)}** | Stop-Loss Price: **${round(exact_sl, 2)}**")
            
            else:
                st.warning(f"⏳ **MARKET SIDEWAYS:** Abhi {pair} range mein fasa hua hai. Koi bhi entry lena risky ho sakta hai, trend clear hone ka wait karein!")
            
            st.markdown("</div>", unsafe_allow_html=True)
                
    if stocks_found == 0:
        st.warning("⚠️ Koi trade current filter match nahi kar raha hai.")

    # Auto Refresh Safety loop
    if auto_refresh:
        time.sleep(185) # slightly higher than JS timer to ensure JS reloads first
        st.rerun()
