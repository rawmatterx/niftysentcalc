import streamlit as st
import streamlit.components.v1 as components

def classify_market_opening(previous_close, sgx_nifty_value):
    if previous_close == 0:
        return "Data Error: Previous close cannot be zero."
    
    percentage_diff = (sgx_nifty_value - previous_close) / previous_close * 100
    flat_threshold = 0.2
    gap_threshold = 0.5

    if abs(percentage_diff) < flat_threshold:
        return "Flat Opening"
    elif abs(percentage_diff) <= gap_threshold:
        return "Gap Up Opening" if percentage_diff > 0 else "Gap Down Opening"
    else:
        return "Huge Gap Up Opening" if percentage_diff > 0 else "Huge Gap Down Opening"

def get_dji_sentiment(change_percentage):
    neutral_band = 0.1
    if change_percentage > neutral_band:
        return "Positive Sentiment"
    elif change_percentage < -neutral_band:
        return "Negative Sentiment"
    return "Neutral Sentiment"

def calculate_close_point(previous_close, change_percentage):
    return previous_close * (1 + (change_percentage / 100))

def determine_market_movement(open_point, close_point):
    if open_point == 0:
        return "Data Error: Open point cannot be zero."
    
    pct_change = ((close_point - open_point) / open_point) * 100
    if pct_change > 1.0:
        return "Bullish Movement"
    elif pct_change < -1.0:
        return "Bearish Movement"
    return "Sideways/Volatile Movement"

def get_market_sentiment(nifty_close, sgx_value, dji_change, vix, dii_buy, fii_net, pcr):
    opening = classify_market_opening(nifty_close, sgx_value)
    dji_sent = get_dji_sentiment(dji_change)
    close_pt = calculate_close_point(nifty_close, dji_change)
    movement = determine_market_movement(sgx_value, close_pt)
    
    high_reward = dii_buy and vix > 25
    bear_trap = fii_net < 0 and pcr < 0.8
    
    return opening, movement, dji_sent, high_reward, bear_trap

# Streamlit UI
st.title("Nifty 50 Sentiment Analyzer - Web Calculator")

components.html("""
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "p1n8m63pzi");
</script>
""", height=0)

with st.form("sentiment_form"):
    col1, col2 = st.columns(2)
    with col1:
        nifty_close = st.number_input("Nifty 50 Previous Close (Spot):", min_value=0.0, step=0.01)
        futures_close = st.number_input("Nifty Futures Previous Close:", min_value=0.0, step=0.01)
        sgx_value = st.number_input("SGX Nifty at 8:45 AM:", min_value=0.0, step=0.01)
        
    with col2:
        dji_change = st.number_input("DJI Change (%):", step=0.01)
        vix = st.number_input("India VIX:", min_value=0.0, step=0.01)
        dii_buy = st.checkbox("DII Net Buying Today")
        fii_net = st.number_input("FII Net Activity (₹ Cr):", help="Negative = Net Selling")
        pcr = st.number_input("PCR Ratio:", min_value=0.0, step=0.01, value=1.0)
    
    analyze_btn = st.form_submit_button("Analyze Market Sentiment")

if analyze_btn:
    if 0 in {nifty_close, futures_close}:
        st.error("Previous close values cannot be zero")
    else:
        # Get sentiment for both spot and futures
        spot_open, spot_move, spot_dji, hr_spot, bt_spot = get_market_sentiment(
            nifty_close, sgx_value, dji_change, vix, dii_buy, fii_net, pcr
        )
        fut_open, fut_move, fut_dji, hr_fut, bt_fut = get_market_sentiment(
            futures_close, sgx_value, dji_change, vix, dii_buy, fii_net, pcr
        )

        # Display predictions
        if spot_open == fut_open and spot_move == fut_move:
            st.success(f"**Consensus Prediction:** {spot_open} → {spot_move} ({spot_dji})")
        else:
            st.warning(f"**Spot Scenario:** {spot_open} → {spot_move} ({spot_dji})")
            st.warning(f"**Futures Scenario:** {fut_open} → {fut_move} ({fut_dji})")

        # Display advanced signals
        if hr_spot or hr_fut:
            st.success("**High-Reward Signal:** DII buying + VIX >25 detected")
        if bt_spot or bt_fut:
            st.warning("**Bear Trap Alert:** FII selling + PCR <0.8 detected")
        
        st.markdown("---")
        st.caption("**Note:** This analysis combines technical indicators with institutional activity patterns. Always verify with fundamental analysis.")

