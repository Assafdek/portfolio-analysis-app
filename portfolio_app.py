import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

@st.cache(ttl=3600, allow_output_mutation=True)
def get_stock_data(ticker, start_date, end_date):
    try:
        # For Australian stocks, try both with and without .AX
        if ticker.upper().endswith('.AX'):
            tickers_to_try = [ticker, ticker[:-3]]
        else:
            tickers_to_try = [ticker, ticker + '.AX']

        for t in tickers_to_try:
            data = yf.download(t, start=start_date, end=end_date, progress=False)
            if not data.empty:
                return data['Close']
        
        st.warning(f"No data available for {ticker}. Please check the ticker symbol.")
        return None
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

def calculate_returns(prices):
    return prices.pct_change().dropna()

def calculate_portfolio_stats(returns, weights):
    portfolio_return = np.sum(returns.mean() * weights) * 252  # Annualized
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    return portfolio_return, portfolio_std

st.title('Portfolio Analysis Tool')

st.sidebar.markdown("""
### Finding Ticker Symbols
- For Australian stocks, you can add '.AX' to the end (e.g., CBA.AX) or leave it off (e.g., CBA)
- ASX tickers: [ASX Website](https://www2.asx.com.au/markets/trade-our-cash-market/directory)
- US tickers: [NASDAQ](https://www.nasdaq.com/market-activity/stocks/screener)
- For other markets: Use [Google Finance](https://www.google.com/finance)
""")

num_stocks = st.number_input('Number of stocks (1-3)', min_value=1, max_value=3, value=1)

tickers = []
weights = []

for i in range(num_stocks):
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input(f'Stock Ticker {i+1}')
    with col2:
        weight = st.number_input(f'Weight {i+1}', min_value=0.0, max_value=1.0, value=1.0/num_stocks)
    tickers.append(ticker)
    weights.append(weight)

weights = np.array(weights)

if st.button('Calculate Portfolio Stats'):
    if np.sum(weights) != 1.0:
        st.error('Weights must sum to 1.0')
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years ago

        all_returns = []
        valid_tickers = []

        for ticker in tickers:
            prices = get_stock_data(ticker, start_date, end_date)
            if prices is not None and not prices.empty:
                returns = calculate_returns(prices)
                all_returns.append(returns)
                valid_tickers.append(ticker)

        if len(all_returns) == len(tickers):
            returns_df = pd.concat(all_returns, axis=1)
            returns_df.columns = valid_tickers

            portfolio_return, portfolio_std = calculate_portfolio_stats(returns_df, weights)

            st.write(f'Expected Annual Return: {portfolio_return:.2%}')
            st.write(f'Annual Standard Deviation: {portfolio_std:.2%}')

            st.line_chart(returns_df.cumsum())

            st.write("Correlation Matrix:")
            correlation_matrix = returns_df.corr()
            st.dataframe(correlation_matrix)
        else:
            st.error("Could not fetch data for all tickers. Please check your inputs and try again.")

st.markdown("""
### Notes:
- Make sure to use correct ticker symbols for each market.
- For Australian stocks, you can add '.AX' to the end (e.g., CBA.AX) or leave it off (e.g., CBA).
- Weights must sum to 1.0 (100%).
- Data is fetched for the last 2 years.
""")
