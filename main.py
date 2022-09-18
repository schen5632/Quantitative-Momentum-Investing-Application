import pandas as pd
import requests
import math
from scipy import stats
from statistics import mean
import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image

IEX_CLOUD_API_TOKEN = 'Tpk_059b97af715d417d9f49f50b51b1c448'
image = Image.open('Screenshot.png')

st.title("Quantitative Momentum Investing Strategy Application")

st.sidebar.header("Upload Stock File")
st.sidebar.image(image)
file = st.sidebar.file_uploader("Please Upload a CSV File following the format above")
st.sidebar.header("Input Portfolio Value")
portfolio_value = st.sidebar.number_input("Please enter the value of the desired portfolio: ")
st.sidebar.header("Input Portfolio Size")
portfolio_size = st.sidebar.number_input("Please enter the number of stocks in the desired portfolio: ", step = 1)

with st.empty():
    while file is None or portfolio_value == 0.0:
        st.write("Please upload a csv file and enter a portfolio value and size on the left sidebar to start")

stocks = pd.read_csv(file)

with st.empty():
    while 'Ticker' not in stocks.columns:
        st.write('The uploaded csv file is invalid. Please upload a csv file with the given format with "Ticker" as the header.')
    st.write("Values Recognized!")

# Building a Momentum Strategy
columns = [
    'Ticker',
    #'Sector',
    'Price',
    'Number of Shares to Buy',
    'One-Year Price Return',
    'One-Year Return Percentile',
    'Six-Month Price Return',
    'Six-Month Return Percentile',
    'Three-Month Price Return',
    'Three-Month Return Percentile',
    'One-Month Price Return',
    'One-Month Return Percentile',
    'Score'
]

df = pd.DataFrame(columns=columns)

# Executing Batch API Call
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


batch = list(chunks(stocks['Ticker'], 100))
tickers = []
for i in range(0, len(batch)):
    tickers.append(','.join(batch[i]))

invalid_stocks = []
for ticker in tickers:
    batch_request_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=stats,quote&symbols={ticker}&token={IEX_CLOUD_API_TOKEN}'
    try:
        response = requests.get(batch_request_url)
        data = response.json()
        for symbol in ticker.split(','):
            try:
                df = df.append(
                    pd.Series(
                        [
                            symbol,
                            # data[symbol]['company']['sector'],
                            data[symbol]['quote']['latestPrice'],
                            'N/A',
                            data[symbol]['stats']['year1ChangePercent'],
                            'N/A',
                            data[symbol]['stats']['month6ChangePercent'],
                            'N/A',
                            data[symbol]['stats']['month3ChangePercent'],
                            'N/A',
                            data[symbol]['stats']['month1ChangePercent'],
                            'N/A',
                            'N/A'
                        ],
                        index=columns), ignore_index=True
                )
            except:
                invalid_stocks.append(symbol)
    except:
        invalid_stocks.append(ticker)


# Calculating Momentum Percentiles
time_periods = [
    'One-Year',
    'Six-Month',
    'Three-Month',
    'One-Month'
]

for row in df.index:
    for time_period in time_periods:
        if df.loc[row, f'{time_period} Price Return'] is None:
            df.loc[row, f'{time_period} Price Return'] = 0.0

for row in df.index:
    for time_period in time_periods:
        df.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(
            df[f'{time_period} Price Return'], df.loc[row, f'{time_period} Price Return']) / 100

# Calculating Score
for row in df.index:
    momentum_percentiles = []
    for time_period in time_periods:
        momentum_percentiles.append(df.loc[row, f'{time_period} Return Percentile'])
    df.loc[row, 'Score'] = mean(momentum_percentiles) * 100

# Selecting Best Momentum Stocks Based on User Input
df.sort_values('Score', ascending=False, inplace=True)
df = df[:portfolio_size]

# Dropping columns
df.drop(columns=['One-Year Price Return', 'One-Year Return Percentile', 'Six-Month Price Return',
                              'Six-Month Return Percentile', 'Three-Month Price Return', 'Three-Month Return Percentile',
                              'One-Month Price Return', 'One-Month Return Percentile', ], inplace = True)
df.reset_index(drop=True)

sumScore = df['Score'].sum()
percent_list = []

index_list = df.index
for i in index_list:
    portfolio_percent = df['Score'][i] / sumScore
    percent_list.append(portfolio_percent * 100)
    portfolio_alloc = portfolio_percent * float(portfolio_value)
    df.loc[i, 'Number of Shares to Buy'] = math.floor(portfolio_alloc / df['Price'][i])

df.insert(3, 'Percentage of Portfolio', percent_list)
test = df['Percentage of Portfolio'].sum()

# Displaying Data
st.write("The following stocks were dropped due to being invalid:", invalid_stocks)

st.subheader('Portfolio')
def convert_df(df):
    # Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

csv = convert_df(df)
st.download_button(
    label="Download Portfolio",
    data=csv,
    file_name='portfolio.csv',
    mime='text/csv',
)

if st.button('Generate Portfolio Pie Chart'):
    labels = df['Ticker'].values
    sizes = df['Percentage of Portfolio'].values
    fig1, ax1 = plt.subplots(figsize=(10, 10))
    ax1.pie(sizes, labels=labels, shadow='True', autopct='%.2f%%')
    ax1.axis('equal')
    st.pyplot(fig1)

st.table(df)
