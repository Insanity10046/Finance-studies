# price=200, sensitivity=0.5
# We need intercepts > 100
demand_params = [50, 150]; # Waiting Buy, Immediate Buy
supply_params = [100, 30]; # Notice the NEGATIVE: sellers only appear if P > 100
sensitivities = [0.5, 0.5];

history = demsetz_model(demand_params, supply_params, sensitivities);
history = history.MARKET(100, 200);
