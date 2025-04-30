def vega(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return 0.0
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * si.norm.pdf(d1) * np.sqrt(T)

# Initial volatility guess
def initial_vol_guess(S, K, T, r):
    guess = np.sqrt(max(2 * abs(np.log(S * np.exp(r*T) / K)) / max(T, 1e-6), 1e-6))
    return float(guess)

# Controlled Newton-Raphson with backtracking
def newton_controlled(f, df, x0, tol=1e-8, max_iters=100, 
                      alpha_start=1.0, alpha_min=1e-6, beta=0.5):
    x = x0
    alpha = alpha_start
    r_old = abs(f(x))
    for iter_num in range(1, max_iters + 1):
        if r_old <= tol:
            break
        dx_full = f(x) / df(x) if df(x) != 0 else 0
        alpha_trial = alpha
        success = False
        while alpha_trial >= alpha_min:
            x_candidate = x - alpha_trial * dx_full
            if x_candidate <= 0:
                alpha_trial *= beta
                continue
            r_new = abs(f(x_candidate))
            if r_new < r_old:
                x = x_candidate
                r_old = r_new
                alpha = min(1.0, alpha_trial / beta)
                success = True
                break
            else:
                alpha_trial *= beta
        if not success:
            return x
    return x

# Vectorized IV calculation
def calc_iv_controlled(row):
    S = row['underlyinglastprice']
    K = row['strike']
    T = row['T']
    price = row['lastprice']
    is_call = (row['right'] == 0)
    if T <= 0 or price <= 0 or pd.isna(S):
        return np.nan
    f = lambda sigma: bs_price(S, K, T, r, sigma, is_call) - price
    df = lambda sigma: vega(S, K, T, r, sigma)
    sigma0 = initial_vol_guess(S, K, T, r)
    try:
        return newton_controlled(f, df, sigma0)
    except Exception:
        return np.nan
