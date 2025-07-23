import yfinance as M_YF
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyextremes import EVA

# download price data
price_data = M_YF.download('SPY', start='1999-01-01', end='2025-01-02', interval='1d')
price_series = price_data['Close', 'SPY'].dropna().astype(float)
# negstive returns for eva to find
daily_returns = price_series.pct_change().dropna() * -1
daily_returns.name = "Negative Daily Returns"

pot_points = [];
pot_continuation = [];
exhaustion_points = [];

# State machine variables
in_extreme_event = False
last_extreme_date = None
# How many days without a new extreme before we declare it "exhausted"
exhaustion_window = 5 # days

def MARK_TO_BENCHMARK():
    fig, ax = plt.subplots(figsize=(14,6))
    ax.plot(price_series.index, price_series, label='SPY Price')
    if pot_points:
        xs, ys = zip(*pot_points)
        ax.scatter(xs, ys, color='red', marker='X', s=100, label='POT Extreme')
        #for x,y in pot_points:
        #    ax.annotate('POT', xy=(x,y), xytext=(0,5), textcoords='offset points', color='red')
            #ax.axvline(x=x, color='red', linestyle='--', alpha=0.6)
    if pot_continuation:
        xs_bm, ys_bm = zip(*pot_continuation)
        ax.scatter(xs_bm, ys_bm, color='blue', marker='o', edgecolors='w', s=80, label='Extreme Continuation')
    if exhaustion_points:
        xs_bmh, ys_bmh = zip(*exhaustion_points)
        ax.scatter(xs_bmh, ys_bmh, color='yellow', marker='o', edgecolors='w', s=80, label='Extreme Exhaust')

    ax.legend()
    plt.show()

def GET_RECENT(today, window, series):
    cutoff = pd.to_datetime(today) - pd.to_timedelta(window)
    recent = series.loc[cutoff:today].dropna()
    return recent

def POT_CHECKER(model, today, price): # checking extremes, and checking its continuation
    if not model.extremes.empty and today.date() in [d.date() for d in model.extremes.index]:
        return True
    else:
        return False;

def POT_CONTINUATION(model,today,price,extreme_today):
    global in_extreme_event, last_extreme_date, exhaustion_window
    if extreme_today and not in_extreme_event:
        print(f"🔴 DETECTED on {today.date()}")
        pot_points.append((today, price))
        in_extreme_event = True;
        last_extreme_date = today;
    if in_extreme_event:
        # We are currently in an extreme event, check if it's over
        if (today - last_extreme_date).days > exhaustion_window:
            # EXHAUSTION: Too much time has passed since the last drop
            print(f"✅ EXHAUSTED on {today.date()}")
            exhaustion_points.append((today, price))
            in_extreme_event = False # Reset the state
        else:
            # CONTINUATION: Still within the event window
            print(f"🟠 CONTINUATION on {today.date()}")
            pot_continuation.append((today, price))


def EXTREME_MODEL(method, recent, param, today):
    model = EVA(recent)
    model.get_extremes(method=method, **param)
    model.fit_model();
    #if today in model.extremes.index:
    return model;
    #return None

# Example loop: daily_returns.index
for today in daily_returns.index:#pd.date_range('1999-01-01', '2025-01-02', freq='7D'):
    recent = GET_RECENT(today, '365D', daily_returns);
    price = price_series.get(today, np.nan);
    # clean recent to fix overflow and invalid value
    recent = recent.dropna();
    recent = recent[np.isfinite(recent)];
    recent = recent.clip(-1e8, 1e8)#np.clip(recent, -1e6, 1e6); # no big numbers
    if recent.empty or len(recent) < 200:
        continue # check again
    price = price_series.get(today, np.nan);
    threshold = recent.quantile(0.9870);
    if threshold <= 0:
        continue
    is_today_extreme = False;
    try:
        with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
            pot_ext = EXTREME_MODEL('POT', recent, {'threshold': threshold, 'r':'7D'}, today);
        is_today_extreme = POT_CHECKER(pot_ext, today, price);
        POT_CONTINUATION(pot_ext,today,price,is_today_extreme);
    except Exception as e:
        # if not e == 'division by zero':
        #    print(today.date(), e)
        pot_ext = None;

#PLOT();
MARK_TO_BENCHMARK();
