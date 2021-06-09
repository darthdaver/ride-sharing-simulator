from os import times
from src.state.RideState import RideState

class Ride:
    def __init__(self, timestamp, reservation):
        self.id = reservation.id
        self.customer_id = reservation.persons[0]
        self.driver_id = ""
        self.from_edge = reservation.fromEdge
        self.to_edge = reservation.toEdge
        self.state = RideState.REQUESTED.value
        self.traci_reservation = reservation
        self.stats = {
            "timestamp_request": timestamp,
            "rejections": 0
        }


    def update_cancel(self, timestamp):
        self.state = RideState.CANCELED.value
        self.stats["timestamp_canceled"] = timestamp


    def update_end(self, timestamp, step):
        self.state = RideState.END.value
        self.stats["end_step"] = step
        self.stats["timestamp_end"] = timestamp
        self.stats["ride_time"] = timestamp - self.stats["timestamp_pickup"]
        # WARNING: for the moment the ride length is equal to the expected one
        self.stats["ride_length"] = self.stats["expected_ride_length"]
        # WARNING: for the moment the waiting length is equal to the expected one
        self.stats["waiting_length"] = self.stats["expected_waiting_length"]
        self.stats["total_time"] = timestamp - self.stats["timestamp_request"]
        self.stats["total_length"] = self.stats["waiting_length"] + self.stats["ride_length"]


    def update_onroad(self, timestamp):
        self.stats["timestamp_pickup"] = timestamp
        self.stats["waiting_time"] = timestamp - self.stats["timestamp_accepted"]


    def update_pending_request(self, e_length, e_travel_time):
        self.state = RideState.PENDING.value
        self.stats["expected_ride_length"] = e_length
        self.stats["expected_ride_time"] = e_travel_time


    def update_pickup(self, timestamp, driver, driver_ride_request, e_price, surge):
        self.driver_id = driver.id
        self.state = RideState.PICKUP.value
        self.stats["expected_waiting_length"] = driver_ride_request["waiting_distance"]
        self.stats["expected_total_length"] = self.stats["expected_ride_length"] + driver_ride_request["waiting_distance"]
        self.stats["expected_waiting_time"] = driver_ride_request["expected_waiting_time"]
        self.stats["expected_total_time"] = driver_ride_request["expected_waiting_time"] + self.stats["expected_ride_time"]
        self.stats["expected_price"] = e_price
        self.stats["timestamp_accepted"] = timestamp
        self.stats["surge_multiplier"] = surge
        self.stats["time_to_accept_request"] = timestamp - self.stats["timestamp_request"]

    def __str__(self):
        #ride_str = '-'*4
        #ride_str += "\nRide\n"
        #ride_str += '-'*4
        #ride_str += '\n'
        ride_str = "\n"
        ride_str += f"  - id: {self.id}\n"
        ride_str += f"  - customer id: {self.customer_id}\n"
        ride_str += f"  - driver id: {self.driver_id}\n"
        ride_str += f"  - from: {self.from_edge}\n"
        ride_str += f"  - to: {self.to_edge}\n"
        ride_str += f"  - state: {self.state}\n"
        ride_str += "   - stats:\n"
        for k, v in self.stats.items():
            ride_str += f"          - {k}: {v}\n"
        #ride_str += '-'*4
        ride_str += '\n'
        return ride_str