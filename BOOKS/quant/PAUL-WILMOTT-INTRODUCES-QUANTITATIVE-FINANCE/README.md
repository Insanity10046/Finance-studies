https://libgen.li/edition.php?id=136003972

This roadmap groups related chapters into four major blocks:

1. **Markets & Instruments** (Ch 1–2)  
2. **Core Pricing Models** (Ch 3–6)  
3. **Advanced Analytics & Exotics** (Ch 7–13)  
4. **Rates, Portfolio & Risk** (Ch 14–19, 21–24)  

---

## 1. Markets & Instruments (Ch 1–2)

| Chapter | ELI5 Summary & Quant‑Trading Use |
|:-------:|:---------------------------------|
| **1. Products & Markets**Equities, Commodities, FX, Forwards & Futures | Learn the “fruits” you can trade—stocks, metal, currencies, forward/future deals—and how their prices evolve. **Quants** need these underlyings for backtests, signals, and hedges. |
| **2. Derivatives** | Instruments whose value “borrows” from underlyings (options, swaps). **Quant traders** build models on these to lock in/arbitrage risk. |

---

## 2. Core Pricing Models (Ch 3–6)

| Chapter | ELI5 Summary & Quant‑Trading Use |
|:-------:|:---------------------------------|
| **3. The Binomial Model** | Think coin‑flip steps for price; works backward to “fair price.” Basis of many discrete pricing/simulation engines. |
| **4. Random Behavior of Assets** | Prices jiggle like a drunkard’s walk—**quant signals** test if patterns deviate from randomness. |
| **5. Elementary Stochastic Calculus** | Math rules for randomness (Ito’s Lemma) let you go from coin flips to continuous models. Underpins Black‑Scholes derivation. |
| **6. The Black–Scholes Model** | A continuous‑time version of the binomial tree: gives closed‑form option prices and deltas for **algorithmic hedging**. |

---

## 3. Advanced Analytics & Exotics (Ch 7–13)

| Chapter | ELI5 Summary & Quant‑Trading Use |
|:-------:|:---------------------------------|
| **7. Partial Differential Equations** | Price‑evolution puzzles become PDEs: **numerical solvers** (finite differences) let quants handle complex payoffs. |
| **8. Black–Scholes Formulae & the Greeks** | The “knobs” (delta, vega, etc.) tell you how option prices wiggle when inputs change—**Greeks** power risk‑management 📊. |
| **9. Volatility Modeling** | Forecast and plug in σ: GARCH, stochastic‑vol, local‑vol surfaces—crucial for volatility‑based strategies. |
| **10. How to Delta Hedge** | Build a dynamic stock‑option combo that neutralizes small moves—your **daily bread** for P&L control. |
| **11. Exotic & Path‑Dependent Options** | Barriers, Asians, lookbacks: exotic payoffs need specialized lattice/Monte Carlo engines. |
| **12. Multi‑Asset Options** | Pricing options on baskets: quants handle correlations and multi‑dimensional PDEs or quasi‑Monte Carlo. |
| **13. Barrier Options** | Knock‑in/knock‑out features; you code “if price crosses this line” logic in your pricing & hedging algo. |

---

## 4. Rates, Portfolio & Risk (Ch 14–19, 21–24)

| Chapter | ELI5 Summary & Quant‑Trading Use |
|:-------:|:---------------------------------|
| **14. Fixed‑Income Products: Yield, Duration & Convexity** | How bond prices move when rates jiggle; **risk managers** and bond quants swear by duration/convexity. |
| **15. Swaps** | Swapping fixed for float cash flows—quants build curve‑stripping and swap‑hedging models. |
| **16. One‑Factor Interest‑Rate Modeling** | Vasicek/Hull‑White assume rates follow simple random process—**rate‑derivative quants** calibrate these to market. |
| **17. Yield Curve Fitting** | Fit smooth curves to discrete bond data (splines, Nelson–Siegel) so your pricing/hedging uses continuous rates. |
| **18. Interest‑Rate Derivatives** | Caps, floors, swaptions—extend Black‑Scholes ideas to rates, needing **vol‑surface** and curve models. |
| **19. HJM & BGM Models** | Advanced “market‑forward” frameworks for rate vol structures—used by banks to price complex IRDs. |
| **21. Portfolio Management** | Mix assets to hit return/risk targets—**mean‑variance**, factor models, backtests inform quant strategies. |
| **22. Value at Risk** | “Worst loss” metric over a time horizon—quants implement VaR engines for risk‑control thresholds. |
| **23. Credit Risk** | Default probabilities & exposures—quants build PD/LGD models and credit‑VaR for bond/CLO trading. |
| **24. RiskMetrics & CreditMetrics** | Industry frameworks for vol/correlation and credit modeling—quants use these as **industry templates**. |
