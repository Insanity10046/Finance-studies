import yfinance as M_YF;
import numpy as M_NP;
import scipy as M_SCI;
import pandas as M_PD
import matplotlib.pyplot as M_PLT;
import bisect
from datetime import datetime, timedelta, date
import math

# -------- VARIABLES --------
price_data = M_YF.download('SPY',start='1999-01-01',end='2025-01-01');
price_series = price_data['Close', 'SPY'].dropna().astype(float)
# negative returns for eva to find
daily_returns = price_series.pct_change().dropna() * -1
daily_returns.name = "Negative Daily Returns"

hawkes_params = (0.1, 0.5, 1.0)
# bool
in_extreme_event = False;
extreme_start_date = None;
# table
extreme_history = [];
extreme_points = [];
extreme_continuation = [];
exhaustion_points = [];
# -------------------- #
#        HELPER        #
# -------------------- #
def GET_RECENT(TODAY, WINDOW, SERIES):
    cutoff = M_PD.to_datetime(TODAY) - M_PD.to_timedelta(WINDOW)
    recent = SERIES.loc[cutoff:TODAY].dropna()
    return recent

def COMPUTE_VAR(THRESHOLD,GENPARETO, ALPHA, FIT_EXCEEDANCE, RECENT):
    #print(FIT_EXCEEDANCE)#, RECENT)
    xi = len(FIT_EXCEEDANCE) / len(RECENT);
    p_gpd = 1 - (1 - ALPHA) / xi
    if 0 <= p_gpd <= 1:
        return THRESHOLD + GENPARETO.ppf(p_gpd)  # GPD quantile
    return THRESHOLD  # Fallback to threshold

def COMPUTE_ES(SHAPE, SCALE, THRESHOLD, VAR):
    if SHAPE < 1:  # ES exists only if shape < 1
        return var + (SCALE - SHAPE * THRESHOLD + SHAPE * VAR) / (1 - SHAPE)
    return M_NP.nan

def hawkes_intensity(events, current_time, mu, alpha, beta):
    total_effect = sum(math.exp(-beta * (current_time - t).days) for t in events if t < current_time)
    return mu + alpha * total_effect

def continuation_probability(lambda_t, delta_t):
    return 1 - math.exp(-lambda_t * delta_t)

def update_parameters(events, current_time, mu, alpha, beta, lr_mu=0.001, lr_alpha=0.001, lr_beta=0.001):
    """Stochastic gradient-like update to adapt Hawkes parameters."""
    time_diffs = [ (current_time - t).days for t in events if t < current_time ]
    if not time_diffs:
        return mu, alpha, beta

    # Compute influence
    effects = [math.exp(-beta * dt) for dt in time_diffs]
    total_effect = sum(effects)

    # Estimate intensity
    lambda_t = mu + alpha * total_effect

    # Gradients (simple approximation)
    grad_mu = 1.0
    grad_alpha = total_effect
    grad_beta = -alpha * sum(dt * e for dt, e in zip(time_diffs, effects))

    # Parameter updates
    mu_new = max(1e-6, mu + lr_mu * (1.0 - lambda_t) * grad_mu)
    alpha_new = max(1e-6, alpha + lr_alpha * (1.0 - lambda_t) * grad_alpha)
    beta_new = max(1e-6, beta + lr_beta * (1.0 - lambda_t) * grad_beta)

    return mu_new, alpha_new, beta_new

def hawkes_adaptive(events, current_time, window_size, mu, alpha, beta, delta_t):
    # Filter events within window
    start_time = current_time - timedelta(days=window_size)
    window_events = [e for e in events if start_time <= e < current_time]

    # Update parameters based on past window
    mu, alpha, beta = update_parameters(window_events, current_time, mu, alpha, beta)

    # Compute intensity and probability
    lambda_t = hawkes_intensity(window_events, current_time, mu, alpha, beta)
    prob = continuation_probability(lambda_t, delta_t)

    return prob, mu, alpha, beta

# -------------------- #
#       FUNCTION       #
# -------------------- #
def MARK_TO_BENCHMARK():
    fig, ax = M_PLT.subplots(figsize=(14,6))
    ax.plot(price_series.index, price_series, label='SPY Price')
    #if extreme_points:
    #    xs, ys = zip(*extreme_points)
    #    ax.scatter(xs, ys, color='red', marker='X', s=100, label='POT Extreme')
        #for x,y in extreme_points:
        #    ax.annotate('POT', xy=(x,y), xytext=(0,5), textcoords='offset points', color='red')
            #ax.axvline(x=x, color='red', linestyle='--', alpha=0.6)
    if extreme_continuation:
        xs_bm, ys_bm = zip(*extreme_continuation)
        ax.scatter(xs_bm, ys_bm, color='blue', marker='o', edgecolors='w', s=80, label='Extreme Continuation')
    #if exhaustion_points:
    #    xs_bmh, ys_bmh = zip(*exhaustion_points)
    #    ax.scatter(xs_bmh, ys_bmh, color='yellow', marker='o', edgecolors='w', s=80, label='Extreme Exhaust')

    ax.legend()
    M_PLT.show()

def FIT_GPD(RETURNS, THRESHOLD):
    exceedances = RETURNS[RETURNS > THRESHOLD] - THRESHOLD
    if len(exceedances) < 10:
        return None,None,None#raise ValueError("Too few exceedances to fit GPD.")

    # Fit the GPD: returns shape, loc (fixed to 0), scale
    shape, loc, scale = M_SCI.stats.genpareto.fit(exceedances, floc=0)
    genpareto = M_SCI.stats.genpareto(c=shape, loc=0, scale=scale)
    return shape, scale, exceedances, genpareto

def IN_EXTREME(TODAY,RETURN, THRESHOLD, VAR, PRICE):
    global in_extreme_event, extreme_start_date
    if not in_extreme_event:

        if RETURN > THRESHOLD and RETURN > VAR:
            in_extreme_event = True;
            extreme_start_date = TODAY.date();
            print(f"🚨 CRASH START: {TODAY.date()} (Loss: {RETURN:.2%})")
            extreme_points.append((TODAY, PRICE))
    else:
        if RETURN <= THRESHOLD:
            print(f"✅ RECOVERY: {TODAY.date()} (Duration: {(TODAY.date() - extreme_start_date).days} days)")
            exhaustion_points.append((TODAY, PRICE))
            in_extreme_event = False;
            extreme_start_date = None;

# -------------------- #
#         LOOP         #
# -------------------- #
mu = 0.1
alpha = 0.5
beta = 1.0

for current in daily_returns.index:
    recent = GET_RECENT(current, '365D', daily_returns).dropna();
    price = price_series.get(current, M_NP.nan);
    # clean recent to fix overflow and invalid value
    recent = recent[M_NP.isfinite(recent)];
    recent = recent.clip(-1e8, 1e8)
    if recent.empty or len(recent) < 200:
        continue # check again
    price = price_series.get(current, M_NP.nan);

    vol_today = recent.std()#vol_tomorrow = FIT_GARCH(recent, 1);

    threshold = recent.quantile(0.964) #* (vol_tomorrow / recent.std()); # fit threshold
    if threshold <= 0:
        continue
    try:
        shape, scale, fit_exceedances, genpareto = FIT_GPD(recent, threshold);
        today_return = daily_returns.get(current, M_NP.nan)
        exceedances = today_return - threshold;
        if not M_NP.isfinite(today_return):
            continue;
        var = COMPUTE_VAR(threshold,genpareto,0.95, fit_exceedances, recent)
        var = COMPUTE_ES(shape,scale,threshold,var)

        is_today_extreme = today_return > var
        # calibrate hawkes process
        if is_today_extreme:#threshold):
            #print(True)
            extreme_history.append(current.date());

        IN_EXTREME(current,today_return, threshold, var, price)
        # predict continuation of extreme
        if in_extreme_event:
            continuation_prob, mu, alpha, beta = hawkes_adaptive(extreme_history,current.date(),365,mu,alpha,beta,5)
            print(continuation_prob)
            if continuation_prob > 0.5:
                extreme_continuation.append((current, price))
                print(f"⚠️ Crash likely to continue (Probability: {continuation_prob:.0%})")
            if (current.date() - extreme_history[-1]).days >= 5:
                extreme_history = []
    except Exception as e:
        error = str(e)
        if error == 'not enough values to unpack (expected 4, got 3)' or error == "object of type 'numpy.float64' has no len()":
            continue
        else:
            print(e)

MARK_TO_BENCHMARK();
# exceedances : today_return - threshold
