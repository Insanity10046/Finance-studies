# region imports
from AlgorithmImports import *
# endregion

def iv_percentile_rank(current_iv, iv_window):
    if len(list(iv_window)) >= 20:  # Ensure you have enough data, e.g., at least 20 days
        #current_iv = float(iv_series.mean())  # Use the mean IV of your current ATM contracts
        iv_history = historical_ivs = [iv_window[i] for i in range(iv_window.Count)]#list(iv_window)  # Your historical IV series
    
        # Calculate IV Percentile: % of days in history where IV was LOWER than today
        iv_percentile = sum(1 for iv in iv_history if iv < current_iv) / len(iv_history) * 100
    
        # Alternative: IV Rank (where current IV sits within the historical range)
        iv_min = min(iv_history)
        iv_max = max(iv_history)
        iv_rank = (current_iv - iv_min) / (iv_max - iv_min) * 100 if (iv_max - iv_min) > 0 else 50
    else:
        iv_percentile = 50  # Default neutral value if not enough data
        iv_rank = 50
    
    return iv_percentile, iv_rank
    ...

class ForexExampleAlgorithm(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2000, 1, 1)
        self.set_end_date(2025, 12, 31)
        self.set_cash(10000);
        # Add the some trading pair.
        self._ticker = self.add_equity("SPXS", Resolution.DAILY); #self.add_cfd("XAUUSD", Resolution.DAILY);#
        #self._ticker.set_leverage(2);
        self._options = self.add_option("SPXS", Resolution.DAILY);
        self._tbill = self.add_equity("BIL", Resolution.DAILY);
        self._cash = self.add_equity("SGOV", Resolution.DAILY);
        
        self.iv_window = RollingWindow(252);
        self.iv_percentile, self.iv_rank = None, None;
        self._sma = self.sma(self._ticker.symbol, 200);
        self._sma_50 = self.sma(self._ticker.symbol, 50);

        self.set_warm_up(30);

    def on_data(self, slice: Slice):
        # Ensure we have quote data in the current slice.
        if self.is_warming_up:
            return;
        if slice.get(self._ticker.symbol) is None:
            return;
        if self._options not in slice.option_chains.keys():
            return;
        chains = slice.option_chains[self._options.symbol];
        if len(chains) == 0 or chains is None:
            return;
        self.dte30 = [c for c in chains if 29 <= (c.expiry.date() - self.time.date()).days]
        if len(self.dte30) == 0 or self.dte30 is None:
            return;
        atm = min(self.dte30, key=lambda c: abs(c.strike - self.securities[self._ticker.symbol].price));
        self.iv_window.add(atm.implied_volatility);
        
        if self.iv_window.is_ready:
            self.iv_percentile, self.iv_rank = iv_percentile_rank(atm.implied_volatility, self.iv_window);
            self.debug(self.iv_percentile);
        
        if slice[self._ticker.symbol].close > self._sma.current.value:
            #self._tbill.set_leverage(1);
            if self.iv_percentile is not None:
                if self.iv_percentile < 50:
                    # use leverage
                    self._ticker.set_leverage(2);
                    # buy
                    self.debug("BUy");
                    self.buy(self._ticker.symbol, 1);
        else:
            self._ticker.set_leverage(1);
            self.liquidate();
        ...
