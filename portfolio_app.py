import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import io

@st.cache_data(ttl=3600)
def get_stock_data(ticker, start_date, end_date):
    base_url = "https://query1.finance.yahoo.com/v7/finance/download/{}"
    params = {
        "period1": int(start_date.timestamp()),
        "period2": int(end_date.timestamp()),
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for suffix in ['', '.AX']:
        try:
            url = base_url.format(ticker + suffix)
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text), parse_dates=['Date'], index_col='Date')
                if not df.empty:
                    return df['Close']
        except Exception as e:
            st.warning(f"Error fetching {ticker + suffix}: {str(e)}")
    
    st.error(f"Could not fetch data for {ticker}")
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
- For Australian stocks, you can add '.AX' to the end (e.g., BHP.AX) or leave it off (e.g., BHP)
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
- For Australian stocks, you can add '.AX' to the end (e.g., BHP.AX) or leave it off (e.g., BHP).
- Weights must sum to 1.0 (100%).
- Data is fetched for the last 2 years.
""")
