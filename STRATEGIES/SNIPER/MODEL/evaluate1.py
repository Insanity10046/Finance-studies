import yfinance as yf
import numpy as np
import tulipy as ta
import pandas as pd

def get_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    if isinstance(data.columns, pd.MultiIndex) and len(ticker) == 1:
        data.columns = data.columns.droplevel(1)
    return data.dropna()

def to_1d(series):
    return np.ascontiguousarray(series.to_numpy(), dtype=np.float64).flatten()
    
def calculate_adx(df, period=14):
    high = to_1d(df['High'])
    low = to_1d(df['Low'])
    close = to_1d(df['Close'])
    
    adx_values = ta.adx(high, low, close, period)
    return pd.Series(adx_values, index=df.index[-len(adx_values):])
def calculate_atr(df, period=14):
    high = to_1d(df['High'])
    low = to_1d(df['Low'])
    close = to_1d(df['Close'])
    
    adx_values = ta.atr(high, low, close, period)
    return pd.Series(adx_values, index=df.index[-len(adx_values):])

def calculate_atr(df, period=14):
    atr_values = ta.atr
def main():
    df = get_data(['AAPL'], '2020-01-01', '2023-01-01')
    adx_series = calculate_adx(df)
    atr_series = calculate_atr(df)
    df['ATR'] = atr_series
    df['ADX'] = adx_series
    print(df[['ATR', 'ADX']].tail())

if __name__ == "__main__":
    main()
