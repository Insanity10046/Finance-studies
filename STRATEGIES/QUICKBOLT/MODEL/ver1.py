import pandas as pd
import yfinance
import numpy as np
from scipy import optimize
import scipy.stats as si
import matplotlib.pyplot as plt
options_data=pd.read_csv("/kaggle/input/spy-daily-eod-options-quotes-2020-2022/spy_2020_2022.csv")
price_data=yfinance.download("SPY", start='2020-01-01',end='2022-02-01', interval='1d')

def historical_volatility():
    price_data['Log_Ret'] = np.log(price_data['Close'] / price_data['Close'].shift(1));
    daily_std = price_data['Log_Ret'].dropna().std()
    price_data['Volatility'] = price_data['Log_Ret'].rolling(window=252).std() * np.sqrt(252)
    volatility = daily_std * np.sqrt(252)
    print(volatility)#price_data.tail(15))

# implied volatility

def implied_vol(spot,strike,expiry,r,marketoptionPrice, types):
    # pricing model
    def bs_price(sigma):
        fx = None
        d1=(np.log(spot/strike)+(r+0.5*sigma**2)*expiry)/(sigma*np.sqrt(expiry))
        d2=d1-(sigma*np.sqrt(expiry))
        BSprice_call=spot*si.norm.cdf(d1,0,1)-strike*np.exp(-r*expiry)*si.norm.cdf(d2,0,1)
        BSprice_put=strike*np.exp(-r*expiry)*si.norm.cdf(-d2)-spot**si.norm.cdf(-d1)
        #print(BSprice_call-marketoptionPrice)
        if types == 'c':
           fx=BSprice_call-marketoptionPrice
        else:
           fx=BSprice_put-marketoptionPrice
        return fx
    low = bs_price(0.0001)
    high = bs_price(100)
    if low * high > 0:
       return None
    return optimize.brentq(bs_price,0.0001,100,maxiter=1000)

options_data['T'] = options_data[' [DTE]'] / 252
def row_iv(row):
    S = float(row[' [UNDERLYING_LAST]'])
    K = float(row[' [STRIKE]'])
    T = float(row['T'])
    if T <= 0:
        return None
    # pick call or put last price
    if not pd.isnull(row[' [C_LAST]']):
        try:
            price = float(row[' [C_LAST]'])
        except ValueError:
            return None;
        opt_type = 'c'
    else:
        try:
            price = float(row[' [P_LAST]'])
        except ValueError:
            return None;
        opt_type = 'p'
    return implied_vol(S, K, T, 0.5, price, opt_type)

options_data['IV_calc'] = options_data.apply(row_iv, axis=1)

print(options_data['IV_calc'])
#print(implied_volatility(15,100,10,1,0.05))
#historical_volatility();
#price_data[['Close', 'Volatility']].plot(subplots=True, color='blue',figsize=(8, 6))
