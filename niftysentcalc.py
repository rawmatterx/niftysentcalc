import streamlit as st
import streamlit.components.v1 as components

# ---------- Helper functions (Revised Scoring) ---------- #

def classify_market_opening(previous_close, gift_nifty_value):
    if previous_close == 0: return "Data Error", 0
    pct_change = (gift_nifty_value - previous_close) / previous_close * 100
    if abs(pct_change) < 0.2:
        return "Flat Opening", 0
    elif abs(pct_change) <= 0.75: # Increased threshold slightly for gap
        return ("Gap Up Opening", 1) if pct_change > 0 else ("Gap Down Opening", -1)
    else:
        return ("Huge Gap Up Opening", 2) if pct_change > 0 else ("Huge Gap Down Opening", -2)

def get_us_individual_points(change_pct):
    if change_pct > 0.2: return 1 # Broadened positive threshold slightly
    if change_pct < -0.2: return -1 # Broadened negative threshold slightly
    return 0

def get_asian_individual_points(change_pct):
    if change_pct > 0.2: return 1
    if change_pct < -0.2: return -1
    return 0

def india_vix_points(vix_level):
    if vix_level == 0: return 0
    if vix_level > 22: return -2 # Increased fear (Doc1 suggests >20-23, Doc2 Source 403)
    if vix_level < 14: return 1  # Lower fear/complacency (Doc1 suggests <15, Doc2 Source 404)
    return 0

def cboe_vix_points(cboe_vix_change_pct):
    if cboe_vix_change_pct > 7: return -1 # Significant spike in US VIX (Doc1 Source 92)
    if cboe_vix_change_pct < -7: return 1
    return 0

def pcr_points(pcr_value):
    if pcr_value == 0: return 0
    if pcr_value > 1.7: return 1    # Contrarian Bullish (Oversold) (Doc1 Src 109,111, Doc2 Src 423)
    if 1.3 < pcr_value <= 1.7: return -1 # Bearish (Doc1 Src 113)
    if 0.7 <= pcr_value <= 1.3: return 0  # Neutral
    if 0.5 <= pcr_value < 0.7: return 1   # Bullish (Doc1 Src 109)
    if pcr_value < 0.5: return -1     # Contrarian Bearish (Overbought/Complacency) (Doc1 Src 113, Doc2 Src 426)
    return 0

def fii_dii_points(net_flow_crores, is_fii=True):
    threshold = 1000 if is_fii else 750 # FII threshold 1000 Cr, DII 750 Cr (Doc1 Src 18, 21)
    if net_flow_crores > threshold: return 1
    if net_flow_crores < -threshold: return -1
    return 0

def crude_oil_points(change_pct):
    if change_pct > 1.5: return -1 # Rising crude negative (Doc1 Src 48, threshold adjusted)
    if change_pct < -1.5: return 1  # Falling crude positive (Doc1 Src 50)
    return 0

def gold_points(change_pct):
    if change_pct > 1: return -1 # Rising gold signals risk aversion (Doc1 Src 54)
    if change_pct < -1: return 1 # Falling gold signals risk-on
    return 0

def usd_inr_fx_points(change_pct): # % change in USD/INR; positive means INR depreciated
    if change_pct > 0.25: return -1 # Rupee depreciation (Doc1 Src 67, threshold adjusted)
    if change_pct < -0.25: return 1 # Rupee appreciation (Doc1 Src 63)
    return 0

def news_sentiment_points(sentiment_str):
    mapping = {"Very Positive": 2, "Positive": 1, "Neutral": 0, "Negative": -1, "Very Negative": -2}
    return mapping.get(sentiment_str, 0)

def major_event_points(event_impact_str):
    mapping = {"Strongly Positive": 2, "Positive": 1, "Neutral": 0, "Negative": -1, "Strongly Negative": -2}
    return mapping.get(event_impact_str, 0)

def previous_day_tech_points(tech_setup_str):
    mapping = {"Strongly Bullish": 2, "Bullish": 1, "Neutral": 0, "Bearish": -1, "Strongly Bearish": -2}
    return mapping.get(tech_setup_str, 0)


def aggregate_sentiment(score):
    # Adjusted thresholds based on a wider potential score range (~max +22 to -22)
    if score >= 8: return "Strongly Bullish"     # Roughly top 25-30% of positive range
    if score >= 3: return "Mildly Bullish"       # Next 30-35%
    if score <= -8: return "Strongly Bearish"
    if score <= -3: return "Mildly Bearish"
    return "Neutral / Range-bound"

# ---------- New: scenario probabilities + narrative (Adjusted thresholds) ---------- #
def scenario_probs(score):
    if score >= 8:   return {"Up": 70, "Side": 20, "Down": 10}
    if score >= 3:   return {"Up": 55, "Side": 30, "Down": 15}
    if score <= -8:  return {"Up": 10, "Side": 20, "Down": 70}
    if score <= -3:  return {"Up": 15, "Side": 30, "Down": 55}
    return {"Up": 33, "Side": 34, "Down": 33} # Neutral

def build_report(tag_open, tag_sent, score, probs, factors, hi_reward_dii_vix, bear_trap_fii_pcr, oversold_bounce_risk):
    primary_scenario = max(probs, key=probs.get)
    # Ensure alt_scenario logic handles cases where multiple scenarios have the min probability
    min_prob = min(probs.values())
    alt_scenarios = [k for k, v in probs.items() if v == min_prob]
    alt_scenario_text = " or ".join(alt_scenarios) # Handles multiple alternate scenarios if probs are equal

    md_report = f"### {tag_open} → **{tag_sent}** \n"
    md_report += f"Composite Sentiment Score: **{score:+}** (details below).  \n\n"
    md_report += "**Probability Matrix (Indicative)** \n"
    md_report += f"- 🔼 Upside Bias: **{probs['Up']}%** \n"
    md_report += f"- ➡️ Sideways/Neutral: **{probs['Side']}%** \n"
    md_report += f"- 🔽 Downside Bias: **{probs['Down']}%** \n\n"
    md_report += f"**Primary Path Outlook:** *{primary_scenario} bias*. Expect price action broadly consistent with {tag_sent.lower()} signals.  \n"
    md_report += f"**Alternate Path Consideration:** If early market dynamics contradict the primary path, observe for a potential shift towards the *{alt_scenario_text}* scenario(s).  \n\n"
    md_report += "**Contributing Factors Score:** \n"
    for factor_name, factor_value in factors.items():
        md_report += f"- {factor_name}: {factor_value:+}  \n"

    md_report += "\n**Special Conditions Noted:**\n"
    conditions_noted = False
    if hi_reward_dii_vix:
        md_report += "✅ *High-Reward Potential*: Significant DII buying when India VIX is elevated (>22) can indicate domestic conviction amidst fear, potentially leading to amplified intraday swings if sentiment turns positive.\n"
        conditions_noted = True
    if bear_trap_fii_pcr:
        md_report += "⚠️ *Bear-Trap Risk*: Notable FII selling combined with a very low Nifty PCR (<0.7) might signal overdone pessimism or retail shorting; susceptible to sharp short-covering rallies.\n"
        conditions_noted = True
    if oversold_bounce_risk:
        md_report += "🔄 *Oversold Bounce Risk?*: A very high Nifty PCR (>1.7) coupled with an elevated India VIX (>20) can suggest extreme pessimism, potentially setting the stage for a technical rebound or short covering.\n"
        conditions_noted = True
    if not conditions_noted:
        md_report += "None of the predefined special conditions met.\n"

    md_report += "\n---\n"
    return md_report

# ---------- Streamlit UI ---------- #
st.set_page_config(layout="wide")
st.title("Nifty 50 Pre-Market Sentiment Analyzer")
st.caption("Based on factors from provided research documents. All interpretations are indicative.")

# Clarity Tracking (Optional - can be removed if not needed)
# components.html("""<script>/* clarity tag trimmed */</script>""", height=0)

with st.form("sentiment_form"):
    st.subheader("Market Data & Global Cues")
    col1, col2, col3 = st.columns(3)
    with col1:
        nifty_prev_close = st.number_input("Nifty 50 Previous Close (Spot)", min_value=0.0, step=0.01, value=22000.0)
        futures_prev_close = st.number_input("Nifty Futures Previous Close", min_value=0.0, step=0.01, value=22050.0)
        gift_nifty_current = st.number_input("GIFT Nifty Current Value (around 8:45 AM IST)", min_value=0.0, step=0.01, value=22100.0)

    with col2:
        dji_change_pct = st.number_input("Dow Jones % Change (Overnight)", step=0.01, format="%.2f", value=0.10)
        sp500_change_pct = st.number_input("S&P 500 % Change (Overnight)", step=0.01, format="%.2f", value=0.15)
        nasdaq_change_pct = st.number_input("Nasdaq % Change (Overnight)", step=0.01, format="%.2f", value=0.20)

    with col3:
        nikkei_change_pct = st.number_input("Nikkei % Change (Live Morning)", step=0.01, format="%.2f", value=0.05)
        hangseng_change_pct = st.number_input("Hang Seng % Change (Live Morning)", step=0.01, format="%.2f", value=-0.10)
        cboe_vix_change_pct = st.number_input("CBOE VIX % Change (Overnight)", step=0.01, format="%.2f", value=1.0)

    st.subheader("Commodities, FX & Volatility (India)")
    col4, col5, col6 = st.columns(3)
    with col4:
        crude_oil_change_pct = st.number_input("Brent Crude % Change (Overnight)", step=0.01, format="%.2f", value=-0.5)
    with col5:
        gold_change_pct = st.number_input("Gold % Change (Overnight)", step=0.01, format="%.2f", value=0.2)
    with col6:
        usd_inr_change_pct = st.number_input("USD/INR % Change (Spot Overnight/Early)", step=0.01, format="%.2f", help="Positive value means INR depreciated", value=0.05)

    st.subheader("Institutional Activity & Derivatives")
    col7, col8, col9 = st.columns(3)
    with col7:
        fii_net_crores = st.number_input("FII Net Investment (₹ Crores)", step=1.0, format="%.0f", value=500.0)
    with col8:
        dii_net_crores = st.number_input("DII Net Investment (₹ Crores)", step=1.0, format="%.0f", value=300.0)
    with col9:
        nifty_pcr_value = st.number_input("Nifty PCR (OI-based)", min_value=0.0, step=0.01, value=1.0, format="%.2f")
        india_vix_level = st.number_input("India VIX Closing Level", step=0.01, value=15.5, format="%.2f")


    st.subheader("Qualitative Factors")
    col10, col11, col12 = st.columns(3)
    with col10:
        news_sentiment_str = st.selectbox("Overall News Sentiment (Overnight & Morning)",
                                          ["Neutral", "Positive", "Very Positive", "Negative", "Very Negative"])
    with col11:
        major_event_impact_str = st.selectbox("Major Overnight Geopolitical/Economic Event Impact",
                                             ["Neutral", "Positive", "Strongly Positive", "Negative", "Strongly Negative"])
    with col12:
        tech_setup_str = st.selectbox("Previous Day's Nifty Technical Setup",
                                      ["Neutral", "Bullish", "Strongly Bullish", "Bearish", "Strongly Bearish"])

    submitted = st.form_submit_button("Analyze Nifty Sentiment")

if submitted:
    # Calculate points for each factor
    pt_dji = get_us_individual_points(dji_change_pct)
    pt_sp500 = get_us_individual_points(sp500_change_pct)
    pt_nasdaq = get_us_individual_points(nasdaq_change_pct)
    us_market_total_pts = pt_dji + pt_sp500 + pt_nasdaq # Combined for simplicity in factor list

    pt_nikkei = get_asian_individual_points(nikkei_change_pct)
    pt_hangseng = get_asian_individual_points(hangseng_change_pct)
    asian_market_total_pts = pt_nikkei + pt_hangseng

    pt_gold = gold_points(gold_change_pct)
    pt_cboe_vix = cboe_vix_points(cboe_vix_change_pct)
    pt_india_vix = india_vix_points(india_vix_level)
    pt_pcr = pcr_points(nifty_pcr_value)
    pt_fii = fii_dii_points(fii_net_crores, is_fii=True)
    pt_dii = fii_dii_points(dii_net_crores, is_fii=False)
    pt_crude = crude_oil_points(crude_oil_change_pct)
    pt_fx = usd_inr_fx_points(usd_inr_change_pct)
    pt_news = news_sentiment_points(news_sentiment_str)
    pt_event = major_event_points(major_event_impact_str)
    pt_tech = previous_day_tech_points(tech_setup_str)

    # Common points for both Spot and Futures analysis (excluding opening gap)
    pts_common_factors = (us_market_total_pts + asian_market_total_pts +
                          pt_gold + pt_cboe_vix + pt_india_vix + pt_pcr +
                          pt_fii + pt_dii + pt_crude + pt_fx +
                          pt_news + pt_event + pt_tech)

    # Spot Analysis
    spot_opening_classification, spot_opening_pts = classify_market_opening(nifty_prev_close, gift_nifty_current)
    spot_final_score = spot_opening_pts + pts_common_factors
    spot_overall_sentiment = aggregate_sentiment(spot_final_score)
    spot_scenario_probabilities = scenario_probs(spot_final_score)

    # Futures Analysis
    futures_opening_classification, futures_opening_pts = classify_market_opening(futures_prev_close, gift_nifty_current)
    futures_final_score = futures_opening_pts + pts_common_factors
    futures_overall_sentiment = aggregate_sentiment(futures_final_score)
    futures_scenario_probabilities = scenario_probs(futures_final_score)

    # Factor list for display
    base_factors_display = {
        "GIFT Nifty Implied Opening": spot_opening_pts, # Will be overwritten for futures report
        "US Markets (Dow, S&P, Nasdaq)": us_market_total_pts,
        "Asian Markets (Nikkei, Hang Seng)": asian_market_total_pts,
        "India VIX Level": pt_india_vix,
        "Nifty PCR": pt_pcr,
        "FII Net Flow": pt_fii,
        "DII Net Flow": pt_dii,
        "Crude Oil Change": pt_crude,
        "Gold Change": pt_gold,
        "USD/INR Change": pt_fx,
        "CBOE VIX Change": pt_cboe_vix,
        "News Sentiment": pt_news,
        "Major Event Impact": pt_event,
        "Previous Day Technicals": pt_tech
    }

    # Special conditions
    dii_buying_high_vix = (dii_net_crores > 0 and india_vix_level > 22)
    fii_selling_low_pcr = (fii_net_crores < 0 and nifty_pcr_value < 0.7)
    pcr_high_vix_high = (nifty_pcr_value > 1.7 and india_vix_level > 20)


    if spot_overall_sentiment == futures_overall_sentiment and spot_opening_classification == futures_opening_classification:
        st.subheader("Consolidated Nifty Sentiment (Spot & Futures Aligned)")
        st.markdown(build_report(spot_opening_classification, spot_overall_sentiment, spot_final_score,
                                 spot_scenario_probabilities, base_factors_display,
                                 dii_buying_high_vix, fii_selling_low_pcr, pcr_high_vix_high))
    else:
        st.subheader("Nifty Spot Sentiment Analysis")
        spot_factors_display = base_factors_display.copy()
        spot_factors_display["GIFT Nifty Implied Opening"] = spot_opening_pts
        st.markdown(build_report(spot_opening_classification, spot_overall_sentiment, spot_final_score,
                                 spot_scenario_probabilities, spot_factors_display,
                                 dii_buying_high_vix, fii_selling_low_pcr, pcr_high_vix_high))

        st.subheader("Nifty Futures Sentiment Analysis")
        futures_factors_display = base_factors_display.copy()
        futures_factors_display["GIFT Nifty Implied Opening"] = futures_opening_pts
        st.markdown(build_report(futures_opening_classification, futures_overall_sentiment, futures_final_score,
                                 futures_scenario_probabilities, futures_factors_display,
                                 dii_buying_high_vix, fii_selling_low_pcr, pcr_high_vix_high))

    st.caption("Disclaimer: This is an indicative tool based on a simplified model and selected factors from research. Probabilities and sentiment aggregations are estimates and should be adjusted with experience and further data. Always conduct your own due diligence before making any trading or investment decisions.")

