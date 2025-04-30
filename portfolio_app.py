import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import time

def get_stock_data(ticker, start_date, end_date, market):
    if market == "Australia" and not ticker.upper().endswith('.AX'):
        formatted_ticker = f"{ticker.upper()}.AX"
    else:
        formatted_ticker = ticker.upper()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = yf.download(formatted_ticker, start=start_date, end=end_date)
            if data.empty:
                raise ValueError("No data found, symbol may be delisted")
            return data['Close']
        except Exception as e:
            if attempt < max_retries - 1:  # i.e. if it's not the last attempt
                time.sleep(5)  # Wait for 5 seconds before retrying
            else:
                st.error(f"Error fetching data for {formatted_ticker}: {str(e)}")
    return None

def calculate_returns(prices):
    return prices.pct_change().dropna()

def calculate_portfolio_stats(returns, weights):
    portfolio_return = np.sum(returns.mean() * weights) * 252  # Annualized
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    return portfolio_return, portfolio_std

def validate_ticker(ticker, market):
    if market == "Australia":
        ticker = ticker.upper()
        if not ticker.endswith('.AX'):
            ticker += '.AX'
    else:
        ticker = ticker.upper()
    
    try:
        info = yf.Ticker(ticker).info
        if info['regularMarketPrice'] is None:
            return None, "Invalid ticker or no data available"
        return ticker, None
    except Exception as e:
        return None, str(e)

# Sidebar with guidance
st.sidebar.markdown("""
### Finding Ticker Symbols
- For Australian stocks, add '.AX' to the end (e.g., BHP.AX)
- ASX tickers: [ASX Website](https://www2.asx.com.au/markets/trade-our-cash-market/directory)
- US tickers: [NASDAQ](https://www.nasdaq.com/market-activity/stocks/screener)
- For other markets: Use [Google Finance](https://www.google.com/finance)

### Market Selection
- Choose the appropriate market for each stock
- For stocks not in Australia or the US, select 'Other'
""")

st.title('Portfolio Analysis Tool')

# User inputs
num_stocks = st.number_input('Number of stocks (1-3)', min_value=1, max_value=3, value=1)

tickers = []
weights = []
markets = []

for i in range(num_stocks):
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input(f'Stock Ticker {i+1}')
    with col2:
        weight = st.number_input(f'Weight {i+1}', min_value=0.0, max_value=1.0, value=1.0/num_stocks)
    with col3:
        market = st.selectbox(f'Market {i+1}', ["Australia", "US", "Other"])
    tickers.append(ticker)
    weights.append(weight)
    markets.append(market)

weights = np.array(weights)

if st.button('Calculate Portfolio Stats'):
    if np.sum(weights) != 1.0:
        st.error('Weights must sum to 1.0')
    else:
        valid_tickers = []
        for ticker, market in zip(tickers, markets):
            valid_ticker, error = validate_ticker(ticker, market)
            if valid_ticker:
                valid_tickers.append(valid_ticker)
            else:
                st.error(f"Error with ticker {ticker}: {error}")

        if len(valid_tickers) != len(tickers):
            st.error("Please correct the ticker symbols before proceeding.")
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=730)  # 2 years ago

            all_returns = []
            for ticker, market in zip(valid_tickers, markets):
                prices = get_stock_data(ticker, start_date, end_date, market)
                if prices is not None:
                    returns = calculate_returns(prices)
                    all_returns.append(returns)

            if len(all_returns) == len(valid_tickers):
                returns_df = pd.concat(all_returns, axis=1)
                returns_df.columns = valid_tickers

                portfolio_return, portfolio_std = calculate_portfolio_stats(returns_df, weights)

                st.write(f'Expected Annual Return: {portfolio_return:.2%}')
                st.write(f'Annual Standard Deviation: {portfolio_std:.2%}')

                st.line_chart(returns_df.cumsum())

                # Display correlation matrix
                st.write("Correlation Matrix:")
                correlation_matrix = returns_df.corr()
                st.dataframe(correlation_matrix)

# Additional information
st.markdown("""
### Notes:
- Make sure to use correct ticker symbols for each market.
- For Australian stocks, the '.AX' suffix will be added automatically if not present.
- Weights must sum to 1.0 (100%).
- Data is fetched for the last 2 years.
""")
