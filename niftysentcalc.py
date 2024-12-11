import streamlit as st
import streamlit.components.v1 as components

def classify_market_opening(nifty50_close, sgx_nifty_value):
    """
    Classify the market opening sentiment based on the percentage difference 
    between the Nifty 50 previous close and the SGX Nifty value.

    Thresholds:
        - If |% difference| < 0.2%: "Flat Opening"
        - If % difference is between 0.2% and 0.5%: "Gap Up Opening" (if positive) or "Gap Down Opening" (if negative)
        - If |% difference| > 0.5%: "Huge Gap Up Opening" (if positive) or "Huge Gap Down Opening" (if negative)
    """
    if nifty50_close == 0:
        return "Data Error: Nifty 50 previous close cannot be zero."
    
    percentage_diff = (sgx_nifty_value - nifty50_close) / nifty50_close * 100

    flat_threshold = 0.2
    gap_threshold = 0.5

    if abs(percentage_diff) < flat_threshold:
        return "Flat Opening"
    elif abs(percentage_diff) <= gap_threshold:
        if percentage_diff > 0:
            return "Gap Up Opening"
        else:
            return "Gap Down Opening"
    else:
        if percentage_diff > 0:
            return "Huge Gap Up Opening"
        else:
            return "Huge Gap Down Opening"


def get_dji_sentiment(change_percentage):
    """
    Determine the DJI sentiment with a small neutral band.
    
    Parameters:
        change_percentage (float): Previous day DJI percentage change.
        
    Returns:
        str: "Positive Sentiment", "Negative Sentiment", or "Neutral Sentiment".
    """
    neutral_band = 0.1  # changes within ±0.1% are neutral
    if change_percentage > neutral_band:
        return "Positive Sentiment"
    elif change_percentage < -neutral_band:
        return "Negative Sentiment"
    else:
        return "Neutral Sentiment"


def calculate_close_point(nifty50_close, change_percentage):
    """
    Calculate the expected close point of the Nifty 50 based on the DJI change percentage.
    
    Parameters:
        nifty50_close (float): Previous day's close of Nifty 50.
        change_percentage (float): DJI previous day's change in percentage.
        
    Returns:
        float: Expected close value of the Nifty 50.
    """
    return nifty50_close * (1 + (change_percentage / 100))


def determine_market_movement(open_point, close_point):
    """
    Determine expected intraday market movement based on percentage difference 
    between the open and the expected close point.
    
    Parameters:
        open_point (float): The indicative open point (e.g., SGX Nifty value).
        close_point (float): The expected close point based on DJI movement.
        
    Returns:
        str: "Bullish Movement" if >2% above open,
             "Bearish Movement" if >2% below open,
             "Sideways/Volatile Movement" otherwise.
    """
    if open_point == 0:
        return "Data Error: Open point cannot be zero."

    difference = close_point - open_point
    pct_change = (difference / open_point) * 100

    bullish_threshold = 2.0   # 2%
    bearish_threshold = -2.0  # -2%

    if pct_change > bullish_threshold:
        return "Bullish Movement"
    elif pct_change < bearish_threshold:
        return "Bearish Movement"
    else:
        return "Sideways/Volatile Movement"


def get_market_sentiment(nifty50_close, sgx_nifty_value, dji_change_percentage):
    """
    Get the overall market sentiment based on the provided data points.
    
    Parameters:
        nifty50_close (float): Nifty 50 previous close value.
        sgx_nifty_value (float): SGX Nifty value at 8:45 AM.
        dji_change_percentage (float): Previous day DJI change in percentage.
        
    Returns:
        tuple: (market_opening_sentiment (str), market_movement (str), dji_sentiment (str))
    """
    market_opening_sentiment = classify_market_opening(nifty50_close, sgx_nifty_value)
    dji_sentiment = get_dji_sentiment(dji_change_percentage)
    close_point = calculate_close_point(nifty50_close, dji_change_percentage)
    market_movement = determine_market_movement(sgx_nifty_value, close_point)
    return market_opening_sentiment, market_movement, dji_sentiment


# ---------------------------------------
# Streamlit Web App
# ---------------------------------------

st.title("Nifty 50 Sentiment Analyzer - Web Calculator")

# Add Microsoft Clarity tracking code
components.html(
    """
    <script type="text/javascript">
        (function(c,l,a,r,i,t,y){
            c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
            t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
            y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
        })(window, document, "clarity", "script", "p1n8m63pzi");
    </script>
    """,
    height=0
)

st.write("Enter the required data points to analyze the Nifty 50 sentiment:")

nifty50_close = st.number_input(
    "Enter Nifty 50 Previous Close Value:",
    min_value=0.0, 
    step=0.01,
    help="This is the previous day's closing value of the Nifty 50 index."
)

sgx_nifty_value = st.number_input(
    "Enter SGX Nifty Value at 8:45 AM:",
    min_value=0.0, 
    step=0.01,
    help="This is the indicative opening value from SGX Nifty futures at 8:45 AM."
)

dji_change_percentage = st.number_input(
    "Enter Dow Jones Industrial Average (DJI) Previous Day Change Percentage:",
    step=0.01,
    help="This is the previous day's percentage change in the DJI index. For example, 0.5 for +0.5%."
)

if st.button("Analyze Nifty 50 Sentiment"):
    # Basic validation
    if nifty50_close == 0:
        st.write("The previous close of Nifty 50 cannot be zero. Please enter a valid number.")
    else:
        sentiment = get_market_sentiment(nifty50_close, sgx_nifty_value, dji_change_percentage)
        if isinstance(sentiment, tuple):
            market_opening_sentiment, market_movement, dji_sentiment = sentiment
            st.write(f"Expected scenario: {market_opening_sentiment}, followed by {market_movement}, with overall {dji_sentiment.lower()}.")
            st.write("**Note:** This analysis is for informational purposes only and not investment advice.")
        else:
            st.write("Unexpected result. Please review the inputs and try again.")
