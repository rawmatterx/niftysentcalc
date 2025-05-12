import streamlit as st
import streamlit.components.v1 as components

# ---------- Helper functions (Revised Scoring based on Research Documents) ---------- #

def classify_market_opening(previous_close, gift_nifty_value):
    """
    Classifies the market opening based on the percentage difference between
    GIFT Nifty value and the previous close.
    Assigns points based on the gap size.
    """
    if previous_close == 0: return "Data Error", 0
    pct_change = (gift_nifty_value - previous_close) / previous_close * 100
    if abs(pct_change) < 0.2: # Threshold for flat opening
        return "Flat Opening", 0
    elif abs(pct_change) <= 0.75: # Threshold for normal gap
        return ("Gap Up Opening", 1) if pct_change > 0 else ("Gap Down Opening", -1)
    else: # Larger gaps
        return ("Huge Gap Up Opening", 2) if pct_change > 0 else ("Huge Gap Down Opening", -2)

def get_us_individual_points(change_pct):
    """ Assigns points based on an individual US market index's overnight percentage change. """
    if change_pct > 0.2: return 1  # Positive sentiment
    if change_pct < -0.2: return -1 # Negative sentiment
    return 0 # Neutral

def get_asian_individual_points(change_pct):
    """ Assigns points based on an individual Asian market index's live morning percentage change. """
    if change_pct > 0.2: return 1  # Positive sentiment
    if change_pct < -0.2: return -1 # Negative sentiment
    return 0 # Neutral

def india_vix_points(vix_level):
    """ Assigns points based on the India VIX level. """
    if vix_level == 0: return 0
    if vix_level > 22: return -2  # High fear (Sources: Doc1 pg5,10,12; Doc2 Sec IV.B)
    if vix_level < 14: return 1   # Low fear/complacency (Sources: Doc1 pg5,10,12; Doc2 Sec IV.B)
    return 0 # Neutral range

def cboe_vix_points(cboe_vix_change_pct):
    """ Assigns points based on the CBOE VIX's overnight percentage change. """
    if cboe_vix_change_pct > 7: return -1 # Significant spike indicates global fear (Doc1 pg5,10)
    if cboe_vix_change_pct < -7: return 1  # Significant drop indicates easing fear
    return 0

def pcr_points(pcr_value):
    """ Assigns points based on Nifty PCR (Put-Call Ratio), including contrarian signals. """
    if pcr_value == 0: return 0
    if pcr_value > 1.7: return 1    # Contrarian Bullish: Oversold (Doc1 pg6,10,13; Doc2 Sec IV.D)
    if 1.3 < pcr_value <= 1.7: return -1 # Bearish
    if 0.7 <= pcr_value <= 1.3: return 0  # Neutral
    if 0.5 <= pcr_value < 0.7: return 1   # Bullish
    if pcr_value < 0.5: return -1     # Contrarian Bearish: Overbought/Complacency
    return 0

def fii_dii_points(net_flow_crores, is_fii=True):
    """ Assigns points based on FII or DII net investment flows. """
    threshold = 1000 if is_fii else 750 # FII threshold 1000 Cr, DII 750 Cr (Doc1 pg2,10)
    if net_flow_crores > threshold: return 1  # Significant net buying
    if net_flow_crores < -threshold: return -1 # Significant net selling
    return 0

def crude_oil_points(change_pct):
    """ Assigns points based on Brent Crude oil's overnight percentage change. """
    if change_pct > 1.5: return -1 # Rising crude is negative for India (Doc1 pg3,10,12)
    if change_pct < -1.5: return 1  # Falling crude is positive
    return 0

def gold_points(change_pct):
    """ Assigns points based on Gold's overnight percentage change. """
    if change_pct > 1.0: return -1 # Rising gold signals risk aversion (Doc1 pg3-4,10,12)
    if change_pct < -1.0: return 1 # Falling gold signals risk-on
    return 0

def usd_inr_fx_points(change_pct):
    """ Assigns points based on USD/INR percentage change. Positive change_pct = INR depreciation. """
    if change_pct > 0.25: return -1 # Significant Rupee depreciation is negative (Doc1 pg4,10,12)
    if change_pct < -0.25: return 1 # Significant Rupee appreciation is positive
    return 0

# Removed qualitative factor functions:
# news_sentiment_points
# major_event_points
# previous_day_tech_points

def aggregate_sentiment(score):
    """ Aggregates the composite score into a sentiment category. Thresholds adjusted for wider score range. """
    # Score range is now smaller as 3 factors (max 2 points each) are removed. Max possible change is -6 to +6.
    # Original range was ~-22 to +22. New range approx -16 to +16.
    # Adjusting thresholds:
    if score >= 6: return "Strongly Bullish" # Adjusted from 8
    if score >= 2: return "Mildly Bullish"   # Adjusted from 3
    if score <= -6: return "Strongly Bearish" # Adjusted from -8
    if score <= -2: return "Mildly Bearish"   # Adjusted from -3
    return "Neutral / Range-bound"

# ---------- Scenario probabilities + Narrative (Adjusted thresholds) ---------- #
def scenario_probs(score):
    """ Provides indicative probabilities for Up, Side, Down scenarios based on the score. """
    # Adjusting thresholds based on new score range:
    if score >= 6:   return {"Up": 70, "Side": 20, "Down": 10} # Adjusted from 8
    if score >= 2:   return {"Up": 55, "Side": 30, "Down": 15} # Adjusted from 3
    if score <= -6:  return {"Up": 10, "Side": 20, "Down": 70} # Adjusted from -8
    if score <= -2:  return {"Up": 15, "Side": 30, "Down": 55} # Adjusted from -3
    return {"Up": 33, "Side": 34, "Down": 33} # Neutral

def build_report(tag_open, tag_sent, score, probs, factors, hi_reward_dii_vix, bear_trap_fii_pcr, oversold_bounce_risk):
    """ Builds the markdown report for the sentiment analysis. """
    primary_scenario = max(probs, key=probs.get)
    min_prob = min(probs.values())
    alt_scenarios = [k for k, v in probs.items() if v == min_prob]
    alt_scenario_text = " or ".join(alt_scenarios)

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
    if oversold_bounce_risk: # (Doc2 Sec IV.D, last para)
        md_report += "🔄 *Oversold Bounce Risk?*: A very high Nifty PCR (>1.7) coupled with an elevated India VIX (>20) can suggest extreme pessimism, potentially setting the stage for a technical rebound or short covering.\n"
        conditions_noted = True
    if not conditions_noted:
        md_report += "None of the predefined special conditions met.\n"

    md_report += "\n---\n"
    return md_report

# ---------- Streamlit UI ---------- #
st.set_page_config(layout="wide") # Use wide layout for more space
st.title("Nifty 50 Pre-Market Sentiment Analyzer (Objective)") # Updated Title
st.caption("Based on quantitative factors from provided research documents. All interpretations are indicative and for educational purposes.")

# Clarity Tracking (Optional)
# components.html("""<script>/* clarity.js script here if you have one */</script>""", height=0)

with st.form("sentiment_form"):
    st.subheader("Market Data & Global Cues")
    col1, col2, col3 = st.columns(3)
    with col1:
        nifty_prev_close = st.number_input("Nifty 50 Previous Close (Spot)", min_value=0.0, step=0.01, value=22000.00)
        futures_prev_close = st.number_input("Nifty Futures Previous Close", min_value=0.0, step=0.01, value=22050.00)
        gift_nifty_current = st.number_input("GIFT Nifty Current Value (around 8:45 AM IST)", min_value=0.0, step=0.01, value=22100.00)

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
        crude_oil_change_pct = st.number_input("Brent Crude % Change (Overnight)", step=0.01, format="%.2f", value=-0.50)
        india_vix_level = st.number_input("India VIX Closing Level", min_value=0.0, step=0.01, value=15.50, format="%.2f")
    with col5:
        gold_change_pct = st.number_input("Gold % Change (Overnight)", step=0.01, format="%.2f", value=0.20)
    with col6:
        usd_inr_change_pct = st.number_input("USD/INR % Change (Spot Overnight/Early)", step=0.01, format="%.2f", help="Positive value means INR depreciated", value=0.05)

    st.subheader("Institutional Activity & Derivatives")
    col7, col8, col9 = st.columns(3)
    with col7:
        fii_net_crores = st.number_input("FII Net Investment (₹ Crores)", step=1.0, format="%.0f", value=500.0)
    with col8:
        dii_net_crores = st.number_input("DII Net Investment (₹ Crores)", step=1.0, format="%.0f", value=300.0)
    with col9:
        nifty_pcr_value = st.number_input("Nifty PCR (OI-based)", min_value=0.0, step=0.01, value=1.00, format="%.2f")

    # Removed Qualitative Factors UI section
    # st.subheader("Qualitative Factors")
    # col10, col11, col12 = st.columns(3) ...

    submitted = st.form_submit_button("Analyze Nifty Sentiment")

if submitted:
    # Calculate points for each factor
    pt_dji = get_us_individual_points(dji_change_pct)
    pt_sp500 = get_us_individual_points(sp500_change_pct)
    pt_nasdaq = get_us_individual_points(nasdaq_change_pct)
    us_market_total_pts = pt_dji + pt_sp500 + pt_nasdaq

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
    # Removed points from qualitative factors:
    # pt_news, pt_event, pt_tech

    # Common points for both Spot and Futures analysis (excluding opening gap points)
    pts_common_factors = (us_market_total_pts + asian_market_total_pts +
                          pt_gold + pt_cboe_vix + pt_india_vix + pt_pcr +
                          pt_fii + pt_dii + pt_crude + pt_fx)
                          # Removed pt_news, pt_event, pt_tech from sum

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

    # Base factor list for display - common elements
    base_factors_display = {
        "GIFT Nifty Implied Opening": 0, # Placeholder
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
        # Removed qualitative factors from display list:
        # "News Sentiment": pt_news,
        # "Major Event Impact": pt_event,
        # "Previous Day Technicals": pt_tech
    }

    # Special conditions check
    dii_buying_high_vix = (dii_net_crores > 0 and india_vix_level > 22)
    fii_selling_low_pcr = (fii_net_crores < -750 and nifty_pcr_value < 0.7)
    pcr_high_vix_high = (nifty_pcr_value > 1.7 and india_vix_level > 20)


    if spot_overall_sentiment == futures_overall_sentiment and spot_opening_classification == futures_opening_classification:
        st.subheader("Consolidated Nifty Sentiment (Spot & Futures Aligned)")
        consolidated_factors = base_factors_display.copy()
        consolidated_factors["GIFT Nifty Implied Opening"] = spot_opening_pts
        st.markdown(build_report(spot_opening_classification, spot_overall_sentiment, spot_final_score,
                                 spot_scenario_probabilities, consolidated_factors,
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

    st.caption("Disclaimer: This is an indicative tool based on a simplified model and selected quantitative factors from the provided research. Probabilities and sentiment aggregations are estimates and should be adjusted with experience and further data. Always conduct your own comprehensive research and due diligence before making any trading or investment decisions.")

