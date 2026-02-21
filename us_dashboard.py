import streamlit as st
import time
from us_backend import run_us_agent

# --- PAGE CONFIG ---
st.set_page_config(page_title="US Stocks Terminal", layout="wide", page_icon="🇺🇸")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0A0A12; color: white; }
    .buy-row { background-color: #003300; padding: 15px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #00FF00; }
    .sell-row { background-color: #330000; padding: 15px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #FF4444; }
    .wait-row { background-color: #1A1A24; padding: 15px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid #555; }
    .big-font { font-size: 19px; font-weight: bold; font-family: 'Courier New', monospace; color: #E0E0E0;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
st.sidebar.title("🇺🇸 US Market Controls")
st.sidebar.markdown("*(Trade on CoinDCX USDC Pairs)*")
use_sim = st.sidebar.checkbox("Simulator Mode", value=True)
sim_balance = st.sidebar.number_input("Virtual Capital ($ USDC)", value=1000)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("✅ Auto-Refresh (60s)", value=True)

st.title("🗽 1% Trader: Wall Street Terminal")
st.markdown("Monitor Top Tech Giants & Crypto Proxies in Real-Time")

if st.button("🔄 MANUAL REFRESH"):
    st.rerun()

# --- MAIN SCANNER ---
status = st.empty()
status.info("📡 Scanning Wall Street Data (Yahoo Finance)...")

# Run Backend Agent
data, real_balance = run_us_agent()
status.empty()

# --- BALANCE DISPLAY ---
current_balance = sim_balance if use_sim else real_balance
lbl = "🎮 Virtual Balance" if use_sim else "💼 Real Wallet Balance"
st.markdown(f"### {lbl}: **$ {current_balance:,.2f} USDC**")
st.markdown("---")

# --- DATA TABLE ---
if not data:
    st.error("❌ US Market Data not available right now. Market might be closed or API is busy.")
else:
    # Headers
    c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1.2, 0.8, 0.8, 2.5])
    c1.write("📈 TICKER")
    c2.write("💵 PRICE (USDC)")
    c3.write("🎯 SIGNAL")
    c4.write("📊 RSI")
    c5.write("🏆 SCORE")
    c6.write("🤖 WALL ST. ANALYSIS")
    st.markdown("---")

    # Rows
    for item in data:
        if "BUY" in item['signal']:
            row_class = "buy-row"
            icon = "🚀"
            sig_color = "#00FF00"
        elif "SELL" in item['signal']:
            row_class = "sell-row"
            icon = "🔻"
            sig_color = "#FF4444"
        else:
            row_class = "wait-row"
            icon = "⏳"
            sig_color = "#AAA"

        # USD Formatting
        p_fmt = f"${item['price']:,.2f}"
        t_fmt = f"${item['target']:,.2f}"
        s_fmt = f"${item['stop_loss']:,.2f}"

        # HTML Row
        with st.container():
            st.markdown(f"""
            <div class="{row_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="width: 15%; font-weight: bold; color: #4DA6FF;">{item['pair']}</div>
                    <div style="width: 15%;" class="big-font">{p_fmt}</div>
                    <div style="width: 15%; font-weight: bold; color: {sig_color};">{icon} {item['signal'].split(' ')[0]}</div>
                    <div style="width: 10%;">{item['rsi']:.1f}</div>
                    <div style="width: 10%; font-weight: bold;">{item['score']}</div>
                    <div style="width: 35%; font-size: 13px; color: #CCC;">{item['reason']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Trade Plan (Only for BUY)
            if "BUY" in item['signal']:
                c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                c1.success(f"Target: {t_fmt}")
                c2.error(f"SL: {s_fmt}")
                
                risk = item['price'] - item['stop_loss']
                if risk > 0:
                    risk_amt = current_balance * 0.02 # 2% Risk rule
                    qty = risk_amt / risk
                    amt = qty * item['price']
                    
                    if amt > current_balance: 
                        amt = current_balance
                        qty = amt / item['price']
                        
                    c3.info(f"Qty: {qty:.4f}")
                    c4.warning(f"Invest: ${amt:,.2f} USDC")
                st.markdown("---")

# --- AUTO REFRESH LOGIC ---
if auto_refresh:
    st.write("") 
    st.markdown("<p style='color:gray; font-size:12px;'>⏳ Next Wall St. scan in 60s...</p>", unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.6) 
        progress_bar.progress(i + 1)
    
    st.rerun()