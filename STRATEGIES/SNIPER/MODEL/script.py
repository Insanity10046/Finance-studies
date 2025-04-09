import yfinance
import ta
from datetime import datetime, timedelta
#data frame
SYMBOL = "SPY";
def get_15m_data(ticker):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=59)  # 59 days = maximum allowed

    data = yfinance.download(ticker, start=start_date, end=end_date, interval='15m')
    return data.dropna()
benchmark = yfinance.download(SYMBOL, start='1999-01-01',end='2024-05-01', interval='1d')
#benchmark = get_15m_data(SYMBOL)
#portfolio setting
intial_capital = 10;
capital = intial_capital;
risk_per_trade = 0.2;
atr_multiplier = 1.5;
entry_price = 0;
stop_loss = 0;
take_profit = 0;
position = None;
losses = 0;
wins = 0;

def indicator(benchmark):
    benchmark['ADX'] = ta.trend.ADXIndicator(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).adx();
    benchmark['+DI'] = ta.trend.ADXIndicator(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).adx_pos();
    benchmark['-DI'] = ta.trend.ADXIndicator(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).adx_neg();
    #benchmark['ADX'] = ta.trend.ADXIndicator.adx(benchmark["ADX"])
    benchmark['ATR'] = ta.volatility.AverageTrueRange(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).average_true_range();
    benchmark['ATR_MA'] = benchmark['ATR'].rolling(window=20).mean()
    benchmark.dropna(inplace=True);
    return benchmark

def strategy(benchmark, i):
    global position, capital, take_profit, stop_loss, entry_price, losses, wins;
    row = benchmark.iloc[i]
    prev_row = benchmark.iloc[i-1]
    adx = row['ADX'].item()
    atr = row['ATR'].item()
    plus_di = row['+DI'].item()
    minus_di = row['-DI'].item()
    crossover1 = ((prev_row['+DI'].item() < prev_row['-DI'].item()) & (plus_di > minus_di))
    crossover2 = ((prev_row['+DI'].item() > prev_row['-DI'].item()) & (plus_di < minus_di))
    high_volatility = atr > row['ATR_MA'].item()
    trend_strength = adx > 25
    if position == None:
        if trend_strength and high_volatility:
            tp_distance = atr * atr_multiplier * 2
            sl_distance = atr * atr_multiplier

            if crossover1:
                entry_price = row['Close'].item();
                position = 'LONG';
                stop_loss = entry_price - sl_distance;
                take_profit = entry_price + tp_distance;
                #print(f"Entered {position} at {entry_price}, SL: {stop_loss}, TP: {take_profit}, DATE: {benchmark.index[i]}")
            if crossover2:
                entry_price = row['Close'].item();
                position = 'SHORT';
                stop_loss = entry_price + sl_distance;
                take_profit = entry_price - tp_distance;
                #print(f"Entered {position} at {entry_price}, SL: {stop_loss}, TP: {take_profit}, DATE: {benchmark.index[i]}")

    elif position == 'LONG':
        if row['Low'].item() <= stop_loss:
            #print(f"{position} exited at index {i}, new capital: {capital}, LOSS")
            losses+=1
            capital -= capital * risk_per_trade;
            position = None;
        elif row['High'].item() >= take_profit:
            wins+=1
            #print(f"{position} exited at index {i}, new capital: {capital}, WIN, DATE: {benchmark.index[i]}")
            capital += capital * risk_per_trade * 2
            position = None;
    elif position == 'SHORT':
        if row['Low'].item() >= take_profit:
            wins+=1
            #print(f"{position} exited at index {i}, new capital: {capital}, WIN, DATE: {benchmark.index[i]}")
            capital += capital * risk_per_trade * 2
            position = None;
        elif row['High'].item() >= stop_loss:
            losses+=1
            #print(f"{position} exited at index {i}, new capital: {capital}, LOSS, DATE: {benchmark.index[i]}")
            capital -= capital * risk_per_trade
            position = None;

def get_metrics():
    years = (benchmark.index.max() - benchmark.index.min()).days / 365.25
    total_return = (capital - intial_capital + intial_capital*risk_per_trade) / intial_capital;
    cagr = (capital - intial_capital)**(1/years) - 1
    
    print(f"intial capital: {intial_capital},     ending capital: {capital}");
    print(f"total returns: {total_return}")
    print(f"cagr: {cagr}")
    
benchmark = indicator(benchmark)

for i in range(1, len(benchmark)):
    if capital > 0:
        strategy(benchmark, i)

get_metrics();
