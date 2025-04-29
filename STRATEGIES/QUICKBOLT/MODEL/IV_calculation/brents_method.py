def black_scholes(spot,strike,expiry,r,marketoptionPrice, types, sigma):
    # pricing model
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


def implied_vol(spot,strike,expiry,r,marketoptionPrice, types):
    f = lambda sigma: black_scholes(spot,strike,expiry,r,marketoptionPrice, types,sigma) 
    a_low = 1e-6
    b_high = 1.0 # intial guess
    # expand upper bound till bracket is found
    while f(a_low) * f(b_high) > 0:
        b_high *= 2;
        if b_high > 100.0:
            result = scipy.optimize.fminbound(lambda σ: abs(f(σ)), 1e-6, 10.0)
            return result;
    
    impv = scipy.optimize.brentq(f, a_low, b_high, xtol = 1e-12)# convergence to 1.84
    return impv

def row_iv(row):
    S = row['underlyinglastprice']# spot price
    K = row['strike']# strike price
    T = row['T']# time
    R = RF_model.get_interest_rate(qb.Time)
    price = None;
    opt_type = None;
    if T <= 0:
        return None
    # pick call or put last price
    if row['right'] == 0:
        price = row['lastprice']
        opt_type = 'c';
    elif row['right'] == 1:
        price = row['lastprice']
        opt_type = 'p'
    return implied_vol(S, K, T, R, price, opt_type)
