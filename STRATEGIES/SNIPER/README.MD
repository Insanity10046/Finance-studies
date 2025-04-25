![1](../SNIPER/thumbnail.png)

A strategy targetting market regime shifts(ADX) in combination with the trend strength(ADX) and movement speed of the trend(volatility: ATR).

measurement model - measurement of trend strength
statistic model - market regime shift
execution model - focus on trade executions under met market conditions

## Sources: 
- ## Data:
 - market charts(OCHLV)
 - trend strength
 - market regimes(sentiment)
 - volatility

## Feature:
- ## Indicators:
- ADX - Trend strength, Market Regime Shifts
- ATR - Volatility measurement, exeuction property assignment(SL, TP)
- ## Metrics:
- Sentiment Analysis

## Model Construction:
- Execution Model(based on: measurement + statistic model)

## Backtesting Framework:
- ## Engine:
- Implement transaction cost framework
- get perfomance metrics and daily P/L
- ## Validation:
- In sample vs Out sample
- Monte Carlo simulation
- Time series Analysis
- Sensitivity Analysis(windows on historical volatility)

## Execution & Monitoring:
- ## Execution:
- Broker API
- Order Scheduler
- ## Monitoring:
- Real time P/L dashboard
