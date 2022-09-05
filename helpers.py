import streamlit as st
import pandas as pd

class Helper_Functions:
    def test(self, file):
        stocks = pd.read_csv(file)
        stocks = stocks[~stocks['Ticker'].isin(['DISCA', 'HFC', 'VIAC', 'WLTW'])]
        st.write(stocks)

