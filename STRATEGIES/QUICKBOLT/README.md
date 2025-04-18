A strategy focusing on volatility model that where multiple strategies will derive from.

volatility model - measurement of sigma(volatility)

## Sources: 
- ## Data:
 - options:
 - Underlying Asset Price History (OHLCV)
 - Calculated Returns Series (for Realized Volatility)
 - Implied Volatility Surface Data
 - Option Greeks (Especially Vega)
 - Risk‑Free Interest Rate Term Structure
 - Dividend Yield Schedules and Forecasts
 - Forward Price Calculations
 - Option Trading Volume & Open Interest
 - Realized Volatility Estimators
 - Time to Expiration & Contract Calendars
 - Cash‑Flow & Credit‑Risk Adjustments

## Feature:
- ## Indicators:
- None as of yet
- ## Metrics:
- calculation of volatility

## Model Construction:
- Measurement Model

## Backtesting Framework:
- ## Engine:
- Implement transaction cost framework
- get perfomance metrics and daily P/L
- ## Validation:
- In sample vs Out sample
- Monte Carlo simulation
- Time series Analysis

## Execution & Monitoring:
- ## Execution:
- Broker API
- Order Scheduler
- ## Monitoring:
- Real time P/L dashboard
