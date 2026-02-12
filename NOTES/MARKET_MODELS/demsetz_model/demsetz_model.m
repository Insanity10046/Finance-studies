classdef demsetz_model
  properties
    # supply and demand for waiting agent
    waiting_supply = 0;
    waiting_demand = 0;

    # supply and demand for immediate agent
    immediate_supply = 0;
    immediate_demand = 0;

    # market parameter
    spread = 0; # implicit cost
    equilibrium_price = 0; # explicit cost

    # sensitivity
    demand_sensitivity = 0;
    supply_sensitivity = 0;
  endproperties;
  methods
    function D = DEMAND(self, price, demand, sensitivity)
      D = max((demand - sensitivity(1) * price), 0);
    endfunction;
    function S = SUPPLY(self, price, supply, sensitivity)
      S = max((supply + sensitivity(2) * price), 0);
    endfunction;

    function equilibrium = TATONEMENT(self, demand, supply, price, max_iter, tolerance, slope, sensitivity)
      potential_price = price;
      converged = false;
      for i = 1:max_iter
        demand_qty = self.DEMAND(potential_price, demand, sensitivity);
        supply_qty = self.SUPPLY(potential_price, supply, sensitivity);
        excess = demand_qty - supply_qty;

        if abs(excess) < tolerance
          equilibrium = potential_price;
          converged = true;
          break;
        endif;
        price_adjustment = slope * excess;
        potential_price = max(potential_price + price_adjustment, 0);
        #if mod(i, 10) == 0
        #  printf("Iter %4d: P = %8.4f, D = %8.4f, S = %8.4f, Z = %8.4f\n",
        #    i, self.potential_price, demand_qty, supply_qty, excess);
        #endif
      endfor;
      if ~converged
        #warning("Tatonnement did not converge in %d iterations", max_iter);
        equilibrium = 0;
      endif
      #self = self;
    endfunction;
    # ==================== CONSTRUCTOR =====================
    function obj = demsetz_model(demand_param, supply_param, sensitivity)
      if nargin > 1
        obj.waiting_demand = demand_param(1); # Demand to BUY from waiters
        obj.immediate_demand = demand_param(2); # Demand to BUY from impatient nigers

        obj.immediate_supply = supply_param(2); # Supply from nigers
        obj.waiting_supply = supply_param(1); # Supply from waiters

        obj.demand_sensitivity = sensitivity(1);
        obj.supply_sensitivity = sensitivity(2);
      endif;
    endfunction;
    # ==================== MARKET =====================
    function equilibrium = BID_PRICE(self, price)
      # demands of waiting agents against supply of immediate agents
      equilibrium = self.TATONEMENT(self.waiting_demand, self.immediate_supply, price, 1000, 1e-4, 0.05, [self.demand_sensitivity, self.supply_sensitivity]);
      ...
    endfunction;
    function equilibrium = ASK_PRICE(self, price)
      # demands of immediate agents against supply of waiting agents
      equilibrium = self.TATONEMENT(self.immediate_demand, self.waiting_supply, price, 1000, 1e-4, 0.05, [self.demand_sensitivity, self.supply_sensitivity]);
      ...
    endfunction;
    function [price_ask, price_bid, spread] = BID_ASK_SPREAD(self, price)
      # difference between the lowest asking price and highest bid price
      price_ask = self.ASK_PRICE(price); # try to find bid price
      price_bid = self.BID_PRICE(price); # try to find ask price

      #printf("ask price: %i\n",price_ask);
      #printf("bid pirce: %i\n",price_bid);

      # check for failed convergence, use demsetz price inducement hypothetical solution
      depth = max(self.waiting_demand + self.waiting_supply, 0.001);
      if price_ask == 0
        # Raise the price to lure in more "Waiting Sellers"
        penalty = 1 / (self.supply_sensitivity * depth)
        price_ask = price * (1 + penalty);
      endif;

      if price_bid == 0
        # Drop the price to lure in more "Waiting Buyers"
        penalty = 1 / (self.demand_sensitivity * depth)
        price_bid = price * (1 - penalty);
      endif;

      spread = price_ask - price_bid;
    endfunction;
    # ==================== MAIN =====================
    function history = MARKET(self, max_time, price)
      current_price = price;
      history = zeros(max_time, 2);

      figure(1);
      clf;

      % Left side: Time-series History
      subplot(2,2,1); title('Price History'); grid on; hold on;
      price_line = plot(NaN, NaN, 'k-', 'LineWidth', 1.5);   % <-- black line
      subplot(2,2,3); title('Spread History'); grid on; hold on;
      spread_line = plot(NaN, NaN, 'r-', 'LineWidth', 1.5); % <-- red line

      % Right side: The Demsetz Double-Cross
      subplot(2, 2, 4); title('Supply and Demand(BID)'); grid on; hold on;
      xlim([0 100]); ylim([0 max(self.waiting_demand, self.immediate_supply)*1.5]);
      bid_demand_line = plot(NaN, NaN, 'b-', 'LineWidth', 1.5);
      bid_supply_line = plot(NaN, NaN, 'r-', 'LineWidth', 1.5);

      subplot(2, 2, 2); title('Supply and Demand(ASK)'); grid on; hold on;
      xlim([0 100]); ylim([0 max(self.immediate_demand, self.waiting_supply)*1.5]);
      ask_demand_line = plot(NaN, NaN, 'b-', 'LineWidth', 1.5);
      ask_supply_line = plot(NaN, NaN, 'r-', 'LineWidth', 1.5);

      for t = 1:max_time
          % 1. Update random shocks for immediate agents (liquidity seekers)
          self.immediate_demand = max((self.immediate_demand + randn() * 2), 0.1);
          self.immediate_supply = max((self.immediate_supply + randn() * 2), 0.1);

          % 2. Calculate Market Prices
          [ask, bid, spread] = self.BID_ASK_SPREAD(current_price);

          % Determine transaction price based on who is more "aggressive"
          if (self.immediate_demand > self.immediate_supply)
              current_price = ask;
          else
              current_price = bid;
          endif

          history(t, :) = [current_price, spread];

          # --- UPDATE ANIMATION ---

          # Plot 1 & 2: Histories
          set(price_line, 'XData', 1:t, 'YData', history(1:t,1));#subplot(2,2,1); plot(t, current_price, 'k.'); xlim([0 max_time]);
          set(spread_line, 'XData', 1:t, 'YData', history(1:t,2));#subplot(2,2,3); plot(t, spread, 'r.'); xlim([0 max_time]);

          # Plot 3: The Double Intersection
          p_range = linspace(0, current_price);
          # SUPPLY AND DEMAND(BID PRICE)
          subplot(2,2,4);

          bid_demands = arrayfun(@(p) self.DEMAND(p, self.waiting_demand, [self.demand_sensitivity, self.supply_sensitivity]), p_range);
          bid_supplies = arrayfun(@(p) self.SUPPLY(p, self.immediate_supply, [self.demand_sensitivity, self.supply_sensitivity]), p_range);

          set(bid_demand_line, 'XData', p_range, 'YData', bid_demands);
          set(bid_supply_line, 'XData', p_range, 'YData', bid_supplies);
          if current_price <= 0
            xlim([0 1]);
          else
            xlim([0 current_price * 1.05]);
          endif
          # SUPPLY AND DEMAND(ASK PRICE)
          subplot(2,2,2);

          ask_demands = arrayfun(@(p) self.DEMAND(p, self.immediate_demand, [self.demand_sensitivity, self.supply_sensitivity]), p_range);
          ask_supplies = arrayfun(@(p) self.SUPPLY(p, self.waiting_supply, [self.demand_sensitivity, self.supply_sensitivity]), p_range);

          set(ask_demand_line, 'XData', p_range, 'YData', ask_demands);
          set(ask_supply_line, 'XData', p_range, 'YData', ask_supplies);
          if current_price <= 0
            xlim([0 1]);
          else
            xlim([0 current_price * 1.05]);
          endif
          % Price range for visualization

          drawnow;
          pause(0.05);
      endfor
    endfunction
  endmethods;
endclassdef;
