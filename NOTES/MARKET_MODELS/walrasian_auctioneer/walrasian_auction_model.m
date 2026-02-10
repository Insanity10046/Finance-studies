classdef walrasian_auction_model
  properties
    # demand
    max_demand = 0;
    demand_sensitivity = 0;
    # supply
    supply = 0;
    supply_sensitivity = 0;
    # other
    potential_price = 0;
    market_clear_price = 0;
    market_clear_quantity = 0;
  endproperties;
  methods
    # ==================== CONSTRUCTOR =====================
    function obj = walrasian_auction_model(demand_param, supply_param)
      if nargin > 1
        obj.max_demand = demand_param(1);
        obj.demand_sensitivity = demand_param(2);
        obj.supply = supply_param(1);
        obj.supply_sensitivity = supply_param(2);
      endif
    endfunction
    # ==================== MARKET =====================
    function D = DEMAND(self, price)
      D = max((self.max_demand - self.demand_sensitivity * price), 0);
    endfunction;
    function S = SUPPLY(self, price)
      S = max((self.supply + self.supply_sensitivity * price), 0);
    endfunction;

    function self = AGGREGATE(self, demands, supplies)
      self.max_demand = sum(demands(:, 1));
      self.demand_sensitivity = sum(demands(:, 2));
      self.supply = sum(supplies(:, 1));
      self.supply_sensitivity = sum(supplies(:, 2));
      self = self;
    endfunction;
    # ==================== MAIN =====================
    function [self, converged] = TATONEMENT(self, price, max_iter, tolerance, slope)
      self.potential_price = price;
      converged = false;
      for i = 1:max_iter
        demand_qty = self.DEMAND(self.potential_price);
        supply_qty = self.SUPPLY(self.potential_price);
        excess = demand_qty - supply_qty;

        if abs(excess) < tolerance
          self.market_clear_quantity = (demand_qty + supply_qty) / 2;
          self.market_clear_price = self.potential_price + 1;
          converged = true;
          printf("\n=== Market Cleared! ===\n");
          printf("Converged at iteration %d: P* = %.4f, Q* = %.4f\n",
            i, self.market_clear_price, self.market_clear_quantity);
          break;
        endif;
        price_adjustment = slope * excess;
        self.potential_price = max(self.potential_price + price_adjustment, 0);
        if mod(i, 10) == 0
          printf("Iter %4d: P = %8.4f, D = %8.4f, S = %8.4f, Z = %8.4f\n",
            i, self.potential_price, demand_qty, supply_qty, excess);
        endif
      endfor;
      if ~converged
        warning("Tatonnement did not converge in %d iterations", max_iter);
      endif
      self = self;
    endfunction;
    # =============================== PLOT ==================================
    function PLOT(self, price_range)
      prices = linspace(price_range(1), price_range(2), 100);
      demands = arrayfun(@(p) self.DEMAND(p), prices);
      supplies = arrayfun(@(p) self.SUPPLY(p), prices);

      figure;
      plot(prices, demands, 'b-', 'LineWidth', 2, 'DisplayName', 'Demand D(P)');
      hold on;
      plot(prices, supplies, 'r-', 'LineWidth', 2, 'DisplayName', 'Supply S(P)');
      # EQUILIBRIUM
      if self.market_clear_price > 0
        plot([self.market_clear_price, self.market_clear_price],
             [0, self.market_clear_quantity], 'k--', 'DisplayName', 'Equilibrium Price');
        plot([0, self.market_clear_price],
             [self.market_clear_quantity, self.market_clear_quantity], 'k--');
        plot(self.market_clear_price, self.market_clear_quantity,
             'ko', 'MarkerSize', 10, 'MarkerFaceColor', 'g', 'DisplayName', 'Equilibrium');
      endif

      xlabel('Price');
      ylabel('Quantity');
      title('Walrasian Auction Model');
      legend('Demand D(P)', 'Supply S(P)', 'Equilibrium');
      grid on;
      hold off;
    endfunction
  endmethods;
endclassdef;
