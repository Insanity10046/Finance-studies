# RESEARCH
from QuantConnect.Research import QuantBook
from AlgorithmImports import *
import datetime
import pandas as pd
import numpy as np

# PORTFOLIO
qb = QuantBook()
qb.SetStartDate(2020, 1, 1);
qb.SetEndDate(2022,1,1);
qb.SetCash(100);

SYMBOL = qb.add_equity("SPY").symbol
OPTION = qb.add_option(SYMBOL)

#DATAS
price_data = qb.History(SYMBOL, 360, Resolution.DAILY)
# option_chain_symbol = option.SYMBOL
print(OPTION.Symbol)
option_chain = qb.OptionChain(SYMBOL)#.option_chains(OPTION.symbol)
SPOT = qb.Securities[SYMBOL].price

def FILTER_CONTRACT(chain, price):#, right):
    #print(sorted(chain))
    contract_symbols = [contract.Symbol for contract in chain]
    #for c in chain:
    #    print(type(c.symbol))
    return contract_symbols
    """
    expiries = sorted({c.expiry for c in chain})
    nearest_expiry = expiries[0]
    filtered_contracts = [c for c in chain if c.expiry == nearest_expiry]
    return filtered_contracts
    """
_filteredcontract = FILTER_CONTRACT(option_chain, SPOT)
print(type(_filteredcontract))

rf_model = ConstantRiskFreeRateInterestRateModel(0.01)#ConstantRateOptionPricingModel(0.01)
div_model = DividendYieldProvider(SYMBOL)#ConstantDividendYieldModel(0.02)

def historical_vol(_data):
    # representation
    price_data['Log_Ret'] = np.log(price_data['close'] / price_data['close'].shift(1))
    price_data['Volatility'] = price_data['Log_Ret'].rolling(window=252).std() * np.sqrt(252)
    # value
    _data['average'] = _data['close'].sum() / _data['close'].count();
    _data['difference'] = _data['close'] - _data['average'];
    _data['squared'] = (_data['difference'])**2
    volatility = np.sqrt(_data['squared'].sum() / _data['close'].count())
    return volatility

historical_vol = historical_vol(price_data);

#price_data[['close', "Volatility"]].plot(subplots=True, color='blue', figsize=(8,6))

# IMPLIED VOLATILITY:
iv_indicators = {};
history = qb.history(_filteredcontract, 20, Resolution.DAILY)
#print(rf_model, div_model.GetDividendYield(datetime(2022,1,1)))
for _symbol in _filteredcontract:
    qb.add_option_contract(_symbol, Resolution.Minute)
    iv_indicators[_symbol] = ImpliedVolatility(_symbol,rf_model,div_model)#qb.iv(_symbol)
#atm = min(_filteredcontract, key=lambda c: abs(c.ID.strike))
#print(atm)
#print(history.index.names)
#print(history.index.get_level_values("symbol").unique()[:5])
# update iv
for _symbol in _filteredcontract:
    #print(_symbol.ID.strike_price)
    #if _symbol not in history.index.get_level_values(0):
    #    continue
    sym_key = _symbol if _symbol in history.index.get_level_values('symbol') else str(_symbol);
    if sym_key not in history.index.get_level_values("symbol"):
        continue
    for dt, row in history.xs(sym_key,level='symbol').iterrows():
        #print(rf_model.get_interest_rate(dt))
        #print(type(dt))
        #print(dt)
        print(type(dt[0]))
        
        price = float(row['close']);
        data = IndicatorDataPoint(sym_key,dt[0].to_pydatetime(),price)
        iv_indicators[_symbol].update(data)

for symbol, iv in iv_indicators.items():
    #if iv.is_ready:
    print(f'{symbol}:IV={iv.current.value}')
#print(iv_indicators.value)
#option_data.head()

