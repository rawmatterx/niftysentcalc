import streamlit as st
import streamlit.components.v1 as components

def classify_market_opening(previous_close, sgx_nifty_value):
    """
    Classify the market opening sentiment based on the percentage difference 
    between the previous close (spot or futures) and the SGX Nifty value.

    Thresholds:
        - If |% difference| < 0.2%: "Flat Opening"
        - If % difference is between 0.2% and 0.5%: "Gap Up Opening" (if positive) or "Gap Down Opening" (if negative)
        - If |% difference| > 0.5%: "Huge Gap Up Opening" (if positive) or "Huge Gap Down Opening" (if negative)
    """
    if previous_close == 0:
        return "Data Error: Previous close cannot be zero."
    
    percentage_diff = (sgx_nifty_value - previous_close) / previous_close * 100

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


def calculate_close_point(previous_close, change_percentage):
    """
    Calculate the expected close point based on the given previous close 
    and the DJI change percentage.
    
    Parameters:
        previous_close (float): Previous close value (spot or futures).
        change_percentage (float): DJI previous day's change in percentage.
        
    Returns:
        float: Expected close value.
    """
    return previous_close * (1 + (change_percentage / 100))


def determine_market_movement(open_point, close_point):
    """
    Determine expected intraday market movement based on percentage difference 
    between the open and the expected close point.
    
    Parameters:
        open_point (float): The indicative open point (e.g., SGX Nifty value).
        close_point (float): The expected close point based on DJI movement.
        
    Returns:
        str: 
            "Bullish Movement" if >1.5% above open,
            "Bearish Movement" if >1.5% below open,
            "Sideways/Volatile Movement" otherwise.
    """
    if open_point == 0:
        return "Data Error: Open point cannot be zero."

    difference = close_point - open_point
    pct_change = (difference / open_point) * 100

    bullish_threshold = 1.5   # 1.5%
    bearish_threshold = -1.5  # -1.5%

    if pct_change > bullish_threshold:
        return "Bullish Movement"
    elif pct_change < bearish_threshold:
        return "Bearish Movement"
    else:
        return "Sideways/Volatile Movement"


def get_market_sentiment(nifty50_close, sgx_nifty_value, dji_change_percentage):
    """
    Get the overall market sentiment based on the provided data points 
    using the given previous close.
    
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
    "Enter Nifty 50 Previous Close Value (Spot):",
    min_value=0.0, 
    step=0.01,
    help="This is the previous day's closing value of the Nifty 50 spot index."
)

futures_close = st.number_input(
    "Enter Nifty 50 Current Month Futures Previous Close Value:",
    min_value=0.0, 
    step=0.01,
    help="This is the previous day's closing value of the Nifty 50 current month futures contract."
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
    # Validate inputs
    if nifty50_close == 0:
        st.write("The previous close of Nifty 50 spot cannot be zero. Please enter a valid number.")
    elif futures_close == 0:
        st.write("The previous close of Nifty Futures cannot be zero. Please enter a valid number.")
    else:
        # Scenario 1 (Spot)
        spot_sentiment = get_market_sentiment(nifty50_close, sgx_nifty_value, dji_change_percentage)
        # Scenario 2 (Futures)
        futures_sentiment = get_market_sentiment(futures_close, sgx_nifty_value, dji_change_percentage)

        if isinstance(spot_sentiment, tuple) and isinstance(futures_sentiment, tuple):
            spot_open, spot_movement, spot_dji = spot_sentiment
            futures_open, futures_movement, futures_dji = futures_sentiment
            
            # Check if both scenarios are the same
            if (spot_open == futures_open and
                spot_movement == futures_movement and
                spot_dji == futures_dji):
                # Both scenarios yield the same result, so just print one scenario
                st.write("**Possible Scenario:**")
                st.write(f"Today, I am expecting a {spot_open} in the market after which a {spot_movement} with {spot_dji}.")
            else:
                # Print both scenarios
                st.write("**Possible Scenarios:**")
                
                st.write("Scenario 1:")
                st.write(f"Today, I am expecting a {spot_open} in the market after which a {spot_movement} with {spot_dji}.")
                
                st.write("")
                
                st.write("Scenario 2:")
                st.write(f"Today, I am expecting a {futures_open} in the market after which a {futures_movement} with {futures_dji}.")

            st.write("**Note:** This analysis is for informational purposes only and not investment advice.")
        else:
            st.write("Unexpected result. Please review the inputs and try again.")

