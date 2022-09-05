import numpy as np
import pandas as pd
import requests
import math
from scipy import stats
import xlsxwriter
from statistics import mean
import streamlit as st
import time
#from secrets import IEX_CLOUD_API_TOKEN


IEX_CLOUD_API_TOKEN = 'Tpk_059b97af715d417d9f49f50b51b1c448'

st.title("Quantitative Momentum Investing Strategy Application")

st.sidebar.header("Upload Stock File")
uploaded_file = st.sidebar.file_uploader("Please Upload a CSV File")
st.sidebar.header("Input Portfolio Value")
portfolio_value = st.sidebar.number_input("Please enter the value of the portfolio: ")

with st.empty():
    while uploaded_file is None or portfolio_value == 0.0:
        st.write("Please upload a csv file and enter a portfolio value to start the program")
    st.write("Values Recognized!")

stocks = pd.read_csv(uploaded_file)
stocks = stocks[~stocks['Ticker'].isin(['DISCA', 'HFC', 'VIAC', 'WLTW'])]
#st.write(stocks)


# Building a Momentum Strategy
hqm_columns = [
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
    'HQM Score'
]

hqm_dataframe = pd.DataFrame(columns = hqm_columns)

# Executing Batch API Call
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=stats,quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        hqm_dataframe = hqm_dataframe.append(
            pd.Series(
            [
                symbol,
                #data[symbol]['company']['sector'],
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
            index = hqm_columns), ignore_index = True
        )

# Calculating Momentum Percentiles
time_periods = [
    'One-Year',
    'Six-Month',
    'Three-Month',
    'One-Month'
]

for row in hqm_dataframe.index:
    for time_period in time_periods:
        if hqm_dataframe.loc[row, f'{time_period} Price Return'] is None:
            hqm_dataframe.loc[row, f'{time_period} Price Return'] = 0.0

for row in hqm_dataframe.index:
    for time_period in time_periods:
        hqm_dataframe.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(
            hqm_dataframe[f'{time_period} Price Return'], hqm_dataframe.loc[row, f'{time_period} Price Return']) / 100

# Print each percentile score to make sure it was calculated properly
for time_period in time_periods:
    print(hqm_dataframe[f'{time_period} Return Percentile'])

# Calculating HQM Score
for row in hqm_dataframe.index:
    momentum_percentiles = []
    for time_period in time_periods:
        momentum_percentiles.append(hqm_dataframe.loc[row, f'{time_period} Return Percentile'])
    hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)

# Selecting 50 Best Momentum Stocks
hqm_dataframe.sort_values('HQM Score', ascending = False, inplace = True)
hqm_dataframe = hqm_dataframe[:50]

# Dropping columns
hqm_dataframe.drop(columns = ['One-Year Price Return', 'One-Year Return Percentile', 'Six-Month Price Return',
                              'Six-Month Return Percentile', 'Three-Month Price Return', 'Three-Month Return Percentile',
                              'One-Month Price Return', 'One-Month Return Percentile',], inplace = True)
hqm_dataframe.reset_index(drop = True)

hqm_sum = hqm_dataframe['HQM Score'].sum()
st.write(hqm_sum)
percent_list = []

index_list = hqm_dataframe.index
for i in index_list:
    portfolio_percent = hqm_dataframe['HQM Score'][i] / hqm_sum
    percent_list.append(portfolio_percent * 100)
    portfolio_alloc = portfolio_percent * float(portfolio_value)
    hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(portfolio_alloc / hqm_dataframe['Price'][i])

hqm_dataframe.insert(3, 'Percentage of Portfolio', percent_list)
test = hqm_dataframe['Percentage of Portfolio'].sum()

#position_size = float(portfolio_value) / len(hqm_dataframe.index)
#for i in range(0, len(hqm_dataframe['Ticker']) - 1):
#    hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / hqm_dataframe['Price'][i])

st.dataframe (hqm_dataframe)

