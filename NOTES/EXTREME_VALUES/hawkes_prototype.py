
import yfinance as M_YF;
import numpy as M_NP;
import scipy as M_SCI;
import pandas as M_PD
import matplotlib.pyplot as M_PLT;
import sklearn as M_SCIKIT
#import arch as M_ARCH
# -------- VARIABLES --------
price_data = M_YF.download('SPY',start='1999-01-01',end='2025-01-01');
price_series = price_data['Close', 'SPY'].dropna().astype(float)
# negative returns for eva to find
daily_returns = price_series.pct_change().dropna() * -1
daily_returns.name = "Negative Daily Returns"
hawkes_params = (0.05, 0.3, 0.7)
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

def hawkes_intensity(current_time: M_PD.Timestamp, event_times: list, params: tuple):
    """
    Compute Hawkes intensity at current time
    λ(t) = μ + α Σ exp(-β(t - t_i)) for t_i < t
    """
    mu, alpha, beta = params
    intensity = mu
    for event_time in event_times:
        if event_time < current_time:
            dt = (current_time - event_time).days
            intensity += alpha * M_NP.exp(-beta * dt)
    return intensity

def forecast_continuation_prob(current_time: M_PD.Timestamp,event_times: list,params: tuple,forecast_horizon: int = 5):
    """
    Forecast probability of continuation events
    E[N(t, t+Δt)] = ∫_t^{t+Δt} λ(s) ds
    """
    mu, alpha, beta = params
    current_intensity = hawkes_intensity(current_time, event_times, params)

    # Expected events in forecast horizon
    expected_events = (
        mu * forecast_horizon +
        (alpha * current_intensity / beta) *
        (1 - M_NP.exp(-beta * forecast_horizon)))

    # Convert to probability (sigmoid transform)
    return 1 / (1 + M_NP.exp(-expected_events))

def fit_hawkes_parameters(event_times: list):
    """MLE estimation of Hawkes parameters"""
    def neg_log_likelihood(params):
        mu, alpha, beta = params
        if alpha >= beta or mu <= 0:  # Stability condition
            return 1e10

        total = 0
        intensity = mu
        for i in range(1, len(event_times)):
            dt = (event_times[i] - event_times[i-1]).days
            total += M_NP.log(intensity) - beta * dt
            intensity = (intensity - mu) * M_NP.exp(-beta * dt) + mu + alpha

        integral = mu * (event_times[-1] - event_times[0]).days
        integral += (alpha/beta) * len(event_times)
        return -(total - integral)

    # Optimize parameters
    res = M_SCI.optimize.minimize(
        neg_log_likelihood,
        hawkes_params,
        bounds=[(1e-5, None), (1e-5, None), (1e-5, None)]
    )
    return res.x
# -------------------- #
#       FUNCTION       #
# -------------------- #
def MARK_TO_BENCHMARK():
    fig, ax = M_PLT.subplots(figsize=(14,6))
    ax.plot(price_series.index, price_series, label='SPY Price')
    if extreme_points:
        xs, ys = zip(*extreme_points)
        ax.scatter(xs, ys, color='red', marker='X', s=100, label='POT Extreme')
        #for x,y in extreme_points:
        #    ax.annotate('POT', xy=(x,y), xytext=(0,5), textcoords='offset points', color='red')
            #ax.axvline(x=x, color='red', linestyle='--', alpha=0.6)
    if extreme_continuation:
        xs_bm, ys_bm = zip(*extreme_continuation)
        ax.scatter(xs_bm, ys_bm, color='blue', marker='o', edgecolors='w', s=80, label='Extreme Continuation')
    if exhaustion_points:
        xs_bmh, ys_bmh = zip(*exhaustion_points)
        ax.scatter(xs_bmh, ys_bmh, color='yellow', marker='o', edgecolors='w', s=80, label='Extreme Exhaust')

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

for today in daily_returns.index:
    recent = GET_RECENT(today, '365D', daily_returns).dropna();
    price = price_series.get(today, M_NP.nan);
    # clean recent to fix overflow and invalid value
    recent = recent[M_NP.isfinite(recent)];
    recent = recent.clip(-1e8, 1e8)
    if recent.empty or len(recent) < 200:
        continue # check again
    price = price_series.get(today, M_NP.nan);

    #vol_tomorrow = FIT_GARCH(recent, 1);

    threshold = recent.quantile(0.964) #* (vol_tomorrow / recent.std()); # fit threshold
    if threshold <= 0:
        continue
    try:
        shape, scale, fit_exceedances, genpareto = FIT_GPD(recent, threshold);
        today_return = daily_returns.get(today, M_NP.nan)
        exceedances = today_return - threshold;
        if not M_NP.isfinite(today_return):
            continue;
        var = COMPUTE_VAR(threshold,genpareto,0.95, fit_exceedances, recent)
        var = COMPUTE_ES(shape,scale,threshold,var)

        is_today_extreme = today_return > var
        # calibrate hawkes process
        if is_today_extreme:#threshold):
            #print(True)
            extreme_history.append(today);
            if len(extreme_history) > 10 and today.month % 3 == 0:
                hawkes_params = fit_hawkes_parameters(extreme_history);

        IN_EXTREME(today,today_return, threshold, var, price)
        # predict continuation of extreme
        if in_extreme_event:
            continuation_prob = forecast_continuation_prob(today, extreme_history,hawkes_params,forecast_horizon=5)
            print(continuation_prob)
            if continuation_prob > 0.5:
                extreme_continuation.append((today, price))
                print(f"⚠️ Crash likely to continue (Probability: {continuation_prob:.0%})")
    except Exception as e:
        error = str(e)
        if error == 'not enough values to unpack (expected 4, got 3)' or error == "object of type 'numpy.float64' has no len()":
            continue
        else:
            print(e)

MARK_TO_BENCHMARK();
# exceedances : today_return - threshold
