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

def vega(sigma, spot,strike,expiry, r):
    d1 = (np.log(spot/strike) + (r+0.5*sigma**2)* expiry / (sigma*np.sqrt(expiry)))
    greek = spot * scipy.stats.norm.pdf(d1) * np.sqrt(expiry)
    return greek

## Vomma is BSM model (f")
def vomma(spot, strike, T , r ,sigma):
    d1 = (np.log(spot / strike) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    greek = vega(sigma,spot,strike,T,r) * (d1) * (d2) / sigma
    return greek

def implied_vol(spot,strike,expiry,r,marketoptionPrice, types, iters, sigma):
    max_iter = iters
    tolerance = 1e-8#0.00000001; # 1e-8
    func = lambda sigma: black_scholes(spot,strike,expiry,r,marketoptionPrice, types, sigma)
    fprime  = lambda sigma: vega(sigma,spot,strike,expiry,r)
    fprime2 = lambda sigma: vomma(spot,strike,expiry,r,sigma)
    
    impv = scipy.optimize.newton(func=func, x0=0.2, fprime=fprime, fprime2=fprime2, tol=1e-12)
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
    return implied_vol(S, K, T, R, price, opt_type, 10, 0.2)

option_data['IV_calc'] = option_data.apply(row_iv, axis=1)

price_data[['close', "Volatility"]].plot(subplots=True, color='blue', figsize=(8,6))
option_data.head()
