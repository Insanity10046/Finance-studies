# region imports
from AlgorithmImports import *
# endregion

class Quickbolt(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2020, 1, 10)
        self.set_end_date(2022, 1, 10)
        self.set_cash(100000)
        self.equity = self.add_equity("SPY", Resolution.MINUTE)
        self.options = self.add_option("SPY", )
        self.iv_indicators = {};

    def on_data(self, slice: Slice):
        if self.portfolio.invested:
            return 
        chain = slice.option_chains.get(self.options.symbol, None)
        if not chain:
            return
        # FILTER CONTRACTS 
        expiry = min([x.expiry for x in chain])
        contracts = sorted([x for x in chain if x.expiry == expiry],
            key=lambda x: abs(chain.underlying.price - x.strike))
        # parameters
        spot = self.securities[self.equity.synbol].price
        atm_strike = min(contracts, key=lambda c:abs(c.strike - spot)).strike
        # get calls and puts(ATM
        call = next((c for c in contracts if c.strike == atm_strike and c.right == OptionRight.CALL), None)
        put = next((c for c in contracts if c.strike == atm_strike and c.right == OptionRight.PUT), None)
        # IV CALCULATION
        if not call or not put:
            return
        for contract in [call,put]:
            if contract.symbol not in self.iv_indicators:
                IV = self.iv(contract.symbol)
                self.iv_indicators[contract.symbol] = IV

            call_iv = self.iv_indicators[call.symbol]
            put_iv = self.iv_indicators[put.symbol]
            # sanity check
            if not call_iv.is_ready or not put_iv.is_ready:
                return
            
            # do conditional statements on IV,
            # lets say for example a straddle strategy if IV is high
            if call_iv.current.value > 0.5 and put_iv.current.value > 0.5:
                # place straddles
                straddles = OptionStrategies.short_straddle(self.options.symbol,atm_strike,expiry)
                self.buy(straddles, 1);
