import ta
from datetime import datetime, timedelta
import numpy as np

# Data frame
SYMBOL = "SPY"
initial_capital = 10
capital = initial_capital
risk_per_trade = 0.2
atr_multiplier = 1.5
entry_price = 0
stop_loss = 0
take_profit = 0
position = None
losses = 0
wins = 0
capital_history = []
trades = []

def get_15m_data(ticker):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=59)  # 59 days = maximum allowed
    data = yfinance.download(ticker, start=start_date, end=end_date, interval='15m')
    return data.dropna()

benchmark = yfinance.download(SYMBOL, start='1999-01-01', end='2024-05-01', interval='1d')

def indicator(benchmark):
    benchmark['ADX'] = ta.trend.ADXIndicator(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).adx()
    benchmark['+DI'] = ta.trend.ADXIndicator(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).adx_pos()
    benchmark['-DI'] = ta.trend.ADXIndicator(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).adx_neg()
    benchmark['ATR'] = ta.volatility.AverageTrueRange(benchmark['High'].squeeze(), benchmark['Low'].squeeze(), benchmark["Close"].squeeze(), 14).average_true_range()
    benchmark['ATR_MA'] = benchmark['ATR'].rolling(window=20).mean()
    benchmark.dropna(inplace=True)
    return benchmark

def strategy(benchmark, i):
    global position, capital, take_profit, stop_loss, entry_price, losses, wins
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
    
    if position is None:
        if trend_strength and high_volatility:
            tp_distance = atr * atr_multiplier * 2
            sl_distance = atr * atr_multiplier
            if crossover1:
                entry_price = row['Close'].item()
                position = 'LONG'
                stop_loss = entry_price - sl_distance
                take_profit = entry_price + tp_distance
                #print(f"Entered {position} at {entry_price}, SL: {stop_loss}, TP: {take_profit}, DATE: {benchmark.index[i]}")
            if crossover2:
                entry_price = row['Close'].item()
                position = 'SHORT'
                stop_loss = entry_price + sl_distance
                take_profit = entry_price - tp_distance
                #print(f"Entered {position} at {entry_price}, SL: {stop_loss}, TP: {take_profit}, DATE: {benchmark.index[i]}")

    elif position == 'LONG':
        if row['Low'].item() <= stop_loss:
            #print(f"{position} exited at index {i}, new capital: {capital}, LOSS")
            losses += 1
            capital -= capital * risk_per_trade
            position = None
            capital_history.append(capital)
        elif row['High'].item() >= take_profit:
            wins += 1
            #print(f"{position} exited at index {i}, new capital: {capital}, WIN, DATE: {benchmark.index[i]}")
            capital += capital * risk_per_trade * 2
            position = None
            capital_history.append(capital)
            
    elif position == 'SHORT':
        if row['Low'].item() >= take_profit:
            wins += 1
            #print(f"{position} exited at index {i}, new capital: {capital}, WIN, DATE: {benchmark.index[i]}")
            capital += capital * risk_per_trade * 2
            position = None
            capital_history.append(capital)
        elif row['High'].item() >= stop_loss:
            losses += 1
            #print(f"{position} exited at index {i}, new capital: {capital}, LOSS, DATE: {benchmark.index[i]}")
            capital -= capital * risk_per_trade
            position = None
            capital_history.append(capital)

def get_metrics():
    years = (benchmark.index.max() - benchmark.index.min()).days / 365.25
    total_return = (capital - initial_capital) / initial_capital
    cagr = (capital / initial_capital) ** (1 / years) - 1 if years > 0 else 0

    # Max Drawdown
    max_drawdown = 0
    peak = initial_capital
    for i in range(1, len(capital_history)):
        if capital_history[i] > peak:
            peak = capital_history[i]
        drawdown = (capital_history[i] - peak) / peak
        max_drawdown = min(max_drawdown, drawdown)

    # Winrate
    winrate = wins / (wins + losses) if (wins + losses) > 0 else 0

    # Average Risk-Reward Ratio
    rr_ratios = []
    for trade in trades:
        if trade['result'] == 'WIN':
            rr = (trade['take_profit'] - trade['entry_price']) / (trade['entry_price'] - trade['stop_loss'])
            rr_ratios.append(rr)
    avg_rr = np.mean(rr_ratios) if rr_ratios else 0

    # Sharpe Ratio
    daily_returns = [(capital_history[i] - capital_history[i-1]) / capital_history[i-1] for i in range(1, len(capital_history))]
    sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) if np.std(daily_returns) > 0 else 0

    # Sortino Ratio
    downside_returns = np.array([r for r in daily_returns if r < 0])
    sortino_ratio = np.mean(daily_returns) / np.std(downside_returns) if np.std(downside_returns) > 0 else 0

    print(f"Initial capital: {initial_capital}, Ending capital: {capital}")
    print(f"Total return: {total_return:.4f} ({total_return * 100:.2f}%)")
    print(f"CAGR: {cagr:.4f} ({cagr * 100:.2f}%)")
    print(f"Max Drawdown: {max_drawdown:.4f} ({max_drawdown * 100:.2f}%)")
    print(f"Winrate: {winrate:.4f} ({winrate * 100:.2f}%)")
    print(f"Average RR: {avg_rr:.4f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
    print(f"Sortino Ratio: {sortino_ratio:.4f}")
    print(f"Total Wins: {wins}, Total Losses: {losses}")
    print(f"Final Capital: {capital}")

# Call functions to backtest and get metrics
benchmark = indicator(benchmark)
for i in range(1, len(benchmark)):
    if capital > 0:
        strategy(benchmark, i)

get_metrics()

#print(f"Number of candles: {len(benchmark)} from {benchmark.index[0]} to {benchmark.index[-1]}")
print(capital, losses, wins)
