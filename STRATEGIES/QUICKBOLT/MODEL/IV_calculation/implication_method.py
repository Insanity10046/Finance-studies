def normalized_price(x, sigma, theta):
    """
    Normalized Black option price:  b(x,σ,θ)
    where x=ln(F/K), θ=+1(call) or -1(put).
    """
    t1 = x/sigma + sigma/2
    t2 = x/sigma - sigma/2
    return theta * math.exp(x/2) * norm.cdf(theta * t1) \
           - theta * math.exp(-x/2) * norm.cdf(theta * t2)


def implied_vol(option_price, forward, strike, time, rates, dividend,option_type, tol: float = 1e-8, max_iter: int = 50):
    delta = np.exp(-r * expiry);
    x = np.log(forward / strike)
    beta = option_price / (delta * np.sqrt(forward*strike))
    theta_flag = 1 if option_type == "call" else -1;
    iota = (1 if theta_flag * x > 0 else 0) * theta_flag * (math.exp(x/2) - math.exp(-x/2))
    if beta < iota:
        return NaN; # option price below intrinsic value
    beta_otm = beta - iota
    theta_flag = theta_flag * (1-2*(1 if x > 0 else 0))
    sigma_c = np.sqrt(2*abs(x));
    bc = normalized_price(x, sigma_c, theta_flag);
    # intial guess
    t_low = (beta_otm - iota) / (bc - iota)
    sigma_low = math.sqrt(2 * x * x / abs(x) - 4 * np.log(t_low));
    u_high = (math.exp(theta_flag * x/2) - beta_otm) / (math.exp(theta_flag * x/2) - bc);
    sigma_high = -2 * norm.ppf(u_high)
    
    u_star = math.exp(theta_flag * x/2) / (math.exp(theta_flag * x/2) - bc)
    sigma_star = -2 * norm.ppf(u_star)
    b_star = normalized_price(x, sigma_star, theta_flag)
    t_lo_star = (b_star - iota) / (bc - iota)
    sigma_star_low = math.sqrt(2 * x * x / (abs(x) - 4 * math.log(t_lo_star)))
    u_hi_star = (math.exp(theta_flag * x/2) - b_star) / (math.exp(theta_flag * x/2) - bc)
    sigma_star_high = -2 * norm.ppf(u_hi_star)
    gamma = math.log((sigma_star - sigma_star_low) / (sigma_star_high - sigma_star_low)) / math.log(b_star / bc)
    w = min(max((beta_otm / bc) ** gamma, 0), 1)
    sigma = (1 - w) * sigma_low + w * sigma_high
    for _ in range(max_iter):
        # function value
        b_val = normalized_price(x, sigma, theta_flag)
        # derivative b' (d b / dσ)
        t1 = x/sigma + sigma/2
        t2 = x/sigma - sigma/2
        b_prime = (math.exp(x/2) * norm.pdf(t1) * (-x/sigma**2 + 0.5)
                   - math.exp(-x/2)* norm.pdf(t2) * (-x/sigma**2 - 0.5))

        # choose Newton step ν and f''/f' ratio
        if beta_otm < bc:
            nu = (math.log((beta_otm - iota)/(b_val - iota))
                  * math.log(b_val - iota)/math.log(beta_otm - iota)
                  * (b_val - iota)/b_prime)
            fpp_over_fp = (x**2/sigma**3 - sigma/4)
            fpp_over_fp -= ((2 + math.log(b_val - iota)) / math.log(b_val - iota)) * (b_prime / (b_val - iota))
        else:
            nu = (beta_otm - b_val) / b_prime
            fpp_over_fp = x**2/sigma**3 - sigma/4

        # Halley correction with step restrictions
        nu_hat = max(nu, -sigma/2)
        eta_hat = max(nu_hat/2 * fpp_over_fp, -0.75)
        delta_sigma = nu_hat / (1 + eta_hat)
        sigma_new = sigma + max(delta_sigma, -sigma/2)

        # convergence check
        if abs(sigma_new/sigma - 1) < tol:
            return sigma_new / sigma_factor
        sigma = sigma_new

    return NaN#raise RuntimeError("Did not converge within max_iter")


def row_iv(row):
    S = row['underlyinglastprice']# spot price
    K = row['strike']# strike price
    T = row['T']# time
    R = RF_model.get_interest_rate(qb.Time)
    price = None;
    opt_type = None;
    forward = S * np.exp((r-q)*T);
    if T <= 0:
        return None
    # pick call or put last price
    if row['right'] == 0:
        price = row['lastprice']
        opt_type = 'call';
    elif row['right'] == 1:
        price = row['lastprice']
        opt_type = 'put'
    return implied_vol(price, forward, K, T, R, div_yield, opt_type)#implied_vol(S, K, T, R, price, opt_type)
