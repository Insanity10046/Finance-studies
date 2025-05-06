import math
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.misc import derivative 
# ---- Constant
DBL_EPSILON = np.finfo(float).eps
SQRT_DBL_EPSILON = np.sqrt(DBL_EPSILON)
MIN_PRICE_THRESHOLD = 1e-40 
MIN_VOL_THRESHOLD = 1e-16 

# ---- Mock Options Data
column = ['expiry(days)','strike','type','bid', 'ask', 'last','IV(actual)']
data = [(30, 100, 0, 3.20, 3.80, 3.50,0.3046),(30,110,0,1.00,1.40,1.20,0.3791), (30,90,0,11.00,11.50,11.30, 0.4309),(60,100,1,2.50,3.00,2.80,0.1760),(60,120,1,5.50,6.20,5.90,0)]

option_data = pd.DataFrame(data,columns=column)

option_data['T'] = option_data['expiry(days)'] / 365
option_data['premium'] = (option_data['bid'] + option_data['ask']) / 2

spot = 100
rfr = 0.015
q = 0 # dividend yield

# --- Normalization & Standard Black Function

def normalized_black(x, sigma):
    """
    Calculates the normalized Black price b(x, sigma).
    Uses standard scipy cdf, NOT the high-accuracy version from the paper.
    Assumes theta=+1 (call option).
    """
    if sigma <= MIN_VOL_THRESHOLD:
        return max(0.0, math.exp(x / 2.0) - math.exp(-x / 2.0))

    try:
        d1 = x / sigma + sigma / 2.0
        d2 = x / sigma - sigma / 2.0
        d1 = max(min(d1, 15.0), -15.0) 
        d2 = max(min(d2, 15.0), -15.0)
    except OverflowError:
         return max(0.0, math.exp(x / 2.0) - math.exp(-x / 2.0)) if x > 0 else 0.0


    exp_x_pos = math.exp(x / 2.0)
    exp_x_neg = math.exp(-x / 2.0)

    price = exp_x_pos * norm.cdf(d1) - exp_x_neg * norm.cdf(d2)

    return max(0.0, price)

def black_vega_normalized(x, sigma):
    if sigma <= MIN_VOL_THRESHOLD:
        return 0.0
    try:
        d1 = x / sigma + sigma / 2.0
        d1 = max(min(d1, 15.0), -15.0)
        term1 = (x / sigma)**2
        term2 = (sigma / 2.0)**2
        exponent_arg = -0.5 * (term1 + term2)
        if exponent_arg < -700:
             return 0.0
        vega = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(exponent_arg)
        return vega
    except (OverflowError, ZeroDivisionError):
         return 0.0

# --- 2. Calculating Branch Points

def calculate_branch_points(x):
    if abs(x) < MIN_VOL_THRESHOLD:
        sigma_c = 0.1
        b_c = normalized_black(x, sigma_c)
        b_prime_c = black_vega_normalized(x, sigma_c)
        b_max = math.exp(x / 2.0)
        if b_prime_c < MIN_VOL_THRESHOLD: # Avoid division by zero
            sigma_l = sigma_c * 0.5
            sigma_u = sigma_c * 1.5
        else:
            sigma_l = sigma_c - b_c / b_prime_c
            sigma_u = sigma_c + (b_max - b_c) / b_prime_c
        sigma_l = max(MIN_VOL_THRESHOLD * 10, sigma_l)

    else:
        sigma_c = math.sqrt(2.0 * abs(x)) # Eq (page 4.1)
        b_c = normalized_black(x, sigma_c) # Eq (page 4.2)
        b_prime_c = black_vega_normalized(x, sigma_c) # Eq (page 4.5) related
        b_max = math.exp(x / 2.0) # Eq (page 2.10)

        if b_prime_c < MIN_VOL_THRESHOLD:
            # fallback
             sigma_l = sigma_c * 0.5
             sigma_u = sigma_c * 1.5
        else:
             sigma_l = sigma_c - b_c / b_prime_c # Eq (page 4.3)
             sigma_u = sigma_c + (b_max - b_c) / b_prime_c # Eq (page 4.4)

        sigma_l = max(MIN_VOL_THRESHOLD * 10, sigma_l)


    b_l = normalized_black(x, sigma_l) # Eq (page 4.7)
    b_u = normalized_black(x, sigma_u) # Eq (page 4.8)

    if not (0 <= b_l < b_c < b_u < b_max):
         sigma_l = sigma_c * 0.7
         sigma_u = sigma_c * 1.3
         b_l = normalized_black(x, sigma_l)
         b_u = normalized_black(x, sigma_u)
         # Re-check b_c placement
         b_c = normalized_black(x, sigma_c)
         b_l = min(b_l, b_c * 0.9)
         b_u = max(b_u, b_c * 1.1)
         b_u = min(b_u, b_max * 0.999) # Ensure b_u < b_max


    return sigma_l, sigma_c, sigma_u, b_l, b_c, b_u, b_max

# --- 3. Simplified Initial Guess

def initial_guess(beta, x, sigma_l, sigma_c, sigma_u, b_l, b_c, b_u, b_max):
# note this part is simplified for educational purposes - @Soujin
    if beta <= 0:
        return MIN_VOL_THRESHOLD * 10
    # Zone 1: Very Low Prices (beta < b_l) - Use inverse of Eq (page 3.3) approx
    if beta < b_l:
        # Simplified inversion of b ~ C * Phi(-|x|/(sqrt(3)*sigma))^3
        # Avoid direct use of Eq 4.38 which relies on the rational approx f_l^rc
        # Fallback: Very rough guess based on scaling towards zero
        # A better simple guess might use Brenner-Subrahmanyam for low prices
        # Or just extrapolate linearly from (0,0) to (b_l, sigma_l)
        # - @Soujin
        guess = sigma_l * (beta / b_l) if b_l > MIN_PRICE_THRESHOLD else sigma_l * 0.5
        return max(MIN_VOL_THRESHOLD * 10, guess)

    # Zone 2: Medium-Low Prices (b_l <= beta <= b_c) - Linear Interpolation
    elif beta <= b_c:
        if abs(b_c - b_l) < MIN_PRICE_THRESHOLD:
             return (sigma_l + sigma_c) / 2.0
        weight = (beta - b_l) / (b_c - b_l)
        guess = sigma_l + weight * (sigma_c - sigma_l)
        return guess

    # Zone 3: Medium-High Prices (b_c < beta <= b_u) - Linear Interpolation, not rational cubic for educational purposes - @Soujin
    elif beta <= b_u:
        if abs(b_u - b_c) < MIN_PRICE_THRESHOLD: 
            return (sigma_c + sigma_u) / 2.0
        weight = (beta - b_c) / (b_u - b_c)
        guess = sigma_c + weight * (sigma_u - sigma_c)
        return guess

    # Zone 4: Very High Prices (b_u < beta < b_max) - Use inverse of Eq (page 3.4) approx
    else: # beta > b_u
        if beta >= b_max - MIN_PRICE_THRESHOLD: 
            return sigma_u * 2.0
        arg_ppf = (b_max - beta) / 2.0
        arg_ppf = max(min(arg_ppf, 1.0 - DBL_EPSILON*10), DBL_EPSILON*10)
        try:
             guess = -2.0 * norm.ppf(arg_ppf)
             guess = max(guess, sigma_u)
             return guess
        except ValueError:
             return sigma_u * (1 + (beta - b_u)/(b_max - b_u)) if (b_max - b_u) > MIN_PRICE_THRESHOLD else sigma_u * 1.5


# --- 4. Objective Function ---

def objective_function_g(sigma_guess, x, market_price_beta, b_l, b_u, b_max):
    current_price = normalized_black(x, sigma_guess)
    effective_b_u = b_u

    # --- Zone 1 Error (Low Prices) ---
    if market_price_beta < b_l:
        # Use logs. Add small constant to avoid log(0).
        safe_beta = max(market_price_beta, MIN_PRICE_THRESHOLD)
        safe_current = max(current_price, MIN_PRICE_THRESHOLD)
        
        if safe_beta <= 0 or safe_current <= 0: return 1e100
        try:
             return math.log(safe_current) - math.log(safe_beta)
        except ValueError:
             return 1e100
    # --- Zone 2 Error (Mid Prices)
    elif market_price_beta <= effective_b_u:
        # Simple difference
        return current_price - market_price_beta

    # --- Zone 3 Error (High Prices)
    else:
        diff_beta = b_max - market_price_beta
        diff_current = b_max - current_price
        safe_diff_beta = max(diff_beta, MIN_PRICE_THRESHOLD)
        safe_diff_current = max(diff_current, MIN_PRICE_THRESHOLD)
        if safe_diff_beta <= 0 or safe_diff_current <= 0: return 1e100
        try:
             if b_max <= current_price: safe_diff_current = MIN_PRICE_THRESHOLD
             if b_max <= market_price_beta: safe_diff_beta = MIN_PRICE_THRESHOLD

             return math.log(safe_diff_current) - math.log(safe_diff_beta)
        except ValueError:
             return 1e100


# --- 5. Householder Iteration (using numerical derivatives)

def householder_step(sigma_n, x, market_price_beta, b_l, b_u, b_max):
    func_g = lambda s: objective_function_g(s, x, market_price_beta, b_l, b_u, b_max)

    dx = max(SQRT_DBL_EPSILON * sigma_n, DBL_EPSILON * 100)
    try:
        g = func_g(sigma_n)

        g_prime = derivative(func_g, sigma_n, dx=dx, n=1, order=3)
        g_double_prime = derivative(func_g, sigma_n, dx=dx, n=2, order=5)
        g_triple_prime = derivative(func_g, sigma_n, dx=dx, n=3, order=7)
    except (ValueError, OverflowError):
        return sigma_n 

    if abs(g_prime) < MIN_VOL_THRESHOLD:
        return sigma_n

    nu = -g / g_prime
    gamma = g_double_prime / g_prime
    delta = g_triple_prime / g_prime

    numerator = 1.0 + 0.5 * gamma * nu
    denominator = 1.0 + nu * (gamma + (1.0/6.0) * delta * nu)

    if abs(denominator) < MIN_VOL_THRESHOLD:
         sigma_n_plus_1 = sigma_n + nu
    else:
         sigma_n_plus_1 = sigma_n + nu * (numerator / denominator)

    sigma_n_plus_1 = max(MIN_VOL_THRESHOLD * 10, sigma_n_plus_1)

    return sigma_n_plus_1

# --- 6. Main Implied Volatility Function

def implied_volatility_lets_be_rational(market_price, F, K, T, option_type='call'):
    if T <= 0 or F <= 0 or K <= 0 or market_price < 0:
        return np.nan 

    # --- Normalization ---
    x = math.log(F / K)
    # Normalize price: beta = P / sqrt(FK)
    sqrt_FK = math.sqrt(F * K)
    if sqrt_FK < MIN_VOL_THRESHOLD: return np.nan 
    beta = market_price / sqrt_FK

    # --- Put-Call Parity / Symmetry ---
    is_call = option_type.lower().startswith('c')
    theta = 1 if is_call else -1

    # Intrinsic value in normalized terms
    intrinsic_normalized = max(0.0, theta * (math.exp(x/2.0) - math.exp(-x/2.0)))

    # Check if price is below intrinsic (arbitrage) - allow tiny tolerance
    if beta < intrinsic_normalized - DBL_EPSILON * 10:
         print(f"Warning: Price {market_price} below intrinsic value.")
         # Return NaN or a very small vol? Paper doesn't explicitly handle arbitrage price. - @Soujin
         return np.nan # arbitrage price often indicates bad input btw

    if not is_call:
        x = -x
    elif x > 0:
        beta = beta - intrinsic_normalized # Use time value
        x = -x # Use reciprocal strike moneyness

    # Now we should have beta corresponding to an OTM call with x <= 0.

    # Check if beta is effectively zero after adjustment
    if beta <= MIN_PRICE_THRESHOLD:
        return MIN_VOL_THRESHOLD # 
    # --- Calculate Branch Points for the (potentially transformed) x ---
    try:
        sigma_l, sigma_c, sigma_u, b_l, b_c, b_u, b_max = calculate_branch_points(x)
    except Exception as e:
        print(f"Error calculating branch points for x={x}: {e}")
        return np.nan

    # Check if price is too high (above max possible price)
    if beta >= b_max - MIN_PRICE_THRESHOLD:
        print(f"Warning: Price {market_price} implies beta {beta} >= b_max {b_max}")
        return np.nan
    # --- Initial Guess ---
    try:
        sigma_0 = initial_guess(beta, x, sigma_l, sigma_c, sigma_u, b_l, b_c, b_u, b_max)
    except Exception as e:
        print(f"Error calculating initial guess for beta={beta}, x={x}: {e}")
        return np.nan

    # --- Two Householder Iterations ---
    try:
        sigma_1 = householder_step(sigma_0, x, beta, b_l, b_u, b_max)
        sigma_2 = householder_step(sigma_1, x, beta, b_l, b_u, b_max)
    except Exception as e:
        print(f"Error during Householder iteration: {e}")
        return np.nan 

    # Final result is sigma = total_volatility = volatility_hat * sqrt(T)
    implied_vol_annualized = sigma_2 / math.sqrt(T)

    # Sanity check the result - avoid extremely large vols
    if implied_vol_annualized > 20.0: # Heuristic limit (2000%)
         print(f"Warning: High implied volatility calculated: {implied_vol_annualized*100:.2f}%")
         # Could return NaN or cap it depending on requirements - @Soujin
         # return np.nan

    return implied_vol_annualized

def row_iv(row):
    S = spot# spot price
    K = row['strike']# strike price
    T = row['T']# time
    R = rfr#RF_model.get_interest_rate(qb.Time)
    price = None;
    opt_type = None;
    forward = S * np.exp((R-q)*T);
    if T <= 0:
        return None
    # pick call or put last price
    if row['type'] == 0:
        price = row['last']
        opt_type = 'call';
    elif row['type'] == 1:
        price = row['last']
        opt_type = 'put'
    return implied_volatility_lets_be_rational(price, forward, K, T, opt_type)
#implied_vol(price, forward, K, T, R, 0, opt_type)

option_data['IV(calc)'] = option_data.apply(row_iv, axis=1)

option_data.head()

# for educational purposes, the script implementation is inaccurate but atleast close by 3 digits. Which is a testament to my capability and my ongoing progress to be a quant. Im proud. Thank you @Soujin for your help aswell. -@Ani(Gamebreaker)

# For more accurate implementation of this model, please use Jaeckel's implementation. 
