p = 1;


# === EXAMPLE 1 NO AGENT
demand_params = [190, 1.2];
supply_params = [1, 0.8];

auctioneer = walrasian_auction_model(demand_params, supply_params);
[auctioneer, success] = auctioneer.TATONEMENT(...
    initial_price = 0,   # Start price
    max_iter = 1000,     # Maximum iterations
    tolerance = 1e-4,     # Convergence tolerance
    slope = 0.05    # Adjustment step or slope
);

auctioneer.PLOT([0, 100]);
#print(auctioneer);
