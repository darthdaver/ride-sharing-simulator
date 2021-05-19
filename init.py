import json
import time
from pathlib import Path

##############################################
#   SIMULATION - PARAMETERS INITIALIZATION   #
##############################################

# customer parameters
with open(Path("repo/customer.json")) as customer_json:
  c_p = json.load(customer_json)

# driver parameters
with open(Path("repo/driver.json")) as driver_json:
  d_p = json.load(driver_json)

# uber parameters
with open(Path("repo/uber.json")) as uber_json:
  u_p = json.load(uber_json)

# simulator parameters
with open(Path("repo/simulator.json")) as simulator_json:
  s_p = json.load(simulator_json)

# net parameters
with open(Path("repo/net.json")) as net_json:
  n_p = json.load(n_p_json)

##################################################
#   END SIMUALTION - PARAMETERS INITIALIZATION   #
##################################################

driver_stats = {
    "average_price_ride": 0,
    "average_driver_gain": 0,
    "average_driver_gain_per_km": 0,
    "average_driver_cost": 0,
    "average_driver_cost_per_km": 0,
    "average_driver_distance_covered_during_activity": 0,
    "average_rides_completed": 0
}

customer_stats = {
    "average_price_ride": 0,
    "average_price_per_km": 0,
    "average_time_to_complete_a_request": 0,
    "canceled_requests": 0,
    "average_waiting_time": 0,
    "average_time_to_accept_request": 0
}

uber_stats = {
    "canceled": [],
    "completed": [],
    "average_prices": [],
    "average_expected_prices": [],
    "average_waiting_times": [],
    "average_ride_times": [],
    "average_total_times": [],
    "average_waiting_lengths": [],
    "average_ride_lengths": [],
    "average_total_lengths": [],
    "average_diff_prices": [],
    "average_diff_waiting_times": [],
    "average_diff_ride_times": [],
    "average_diff_total_times": [],
    "average_diff_waiting_lengths": [],
    "average_diff_ride_lengths": [],
    "average_diff_total_lengths": [],
    "average_surge_multipliers": [],
    "average_balances": [],
    "average_rejections": []
}