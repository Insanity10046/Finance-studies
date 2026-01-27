# region imports
from AlgorithmImports import *
# endregion

class ForexExampleAlgorithm(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2000, 1, 1)
        self.set_end_date(2011, 12, 31)
        self.set_cash(10000);
        # Add the some trading pair.
        self._ticker = self.add_equity("SPY", Resolution.DAILY);#self.add_equity("SPY", Resolution.DAILY);
        
        self._atr = self.atr(self._ticker.symbol, 14);
        self._atr_sma = SimpleMovingAverage(20);
        self._atr_sma_mean = SimpleMovingAverage(50);
        self._atr.updated += self.on_atr_update;
        
        self._adx = self.adx(self._ticker.symbol, 14);
        self._sma = self.sma(self._ticker.symbol, 200);

        self.set_warm_up(30);

    def on_data(self, slice: Slice):
        # Ensure we have quote data in the current slice.
        if self.is_warming_up:
            return;
        if slice.get(self._ticker.symbol) is None:
            return;
        
        mean = self._atr_sma_mean.current.value;
        high_vol = self._atr.current.value > mean;
        if slice[self._ticker.symbol].close > self._sma.current.value:
            # use leverage
            self._ticker.set_leverage(2);
            self.debug("BUy");
            self.buy(self._ticker.symbol, 1);
        else:
            self._ticker.set_leverage(1);
            self.liquidate();
        ...
    
    def on_atr_update(self, sender, updated: IndicatorDataPoint):
        self._atr_sma.update(updated.end_time, float(updated.value));
        if self._atr_sma.is_ready:
            self._atr_sma_mean.update(updated.end_time, float(self._atr_sma.current.value));
