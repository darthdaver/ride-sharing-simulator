import json
import os
from src.model.Map import Map
from src.state.DriverState import DriverState
from src.state.RideState import RideState
from src.state.RideRequestState import RideRequestState
from src.utils import utils

class Provider:
    def __init__(self, provider_setup):
        self.__rides = {}
        self.__fare = provider_setup["fare"]
        self.__request = provider_setup["request"]
        self.__unprocessed_requests = []
        self.__pending_customers = []

    def add_ride(self, ride):
        self.__rides[ride.get_id()] = ride

    def add_candidate_to_ride(self, ride_id, driver_candidate):
        self.__rides[ride_id].add_driver_candidate(driver_candidate)

    def print_rides_number(self):
        print(len(self.__rides.keys()))

    def compute_price(self, travel_time, ride_length, surge_multiplier):
        base_fare = self.__fare["base_fare"]
        fee_per_minute = self.__fare["fee_per_minute"]
        fee_per_mile = self.__fare["fee_per_mile"]
        price = (base_fare + (fee_per_minute * travel_time) + (fee_per_mile * ride_length/1000)) * surge_multiplier
        return price

    @staticmethod
    def get_idle_drivers_info(drivers_info):
        drivers_info_array = drivers_info.values()
        idle_drivers_info = filter(lambda d: d.state in [DriverState.IDLE, DriverState.MOVING])
        return idle_drivers_info

    def get_pending_rides(self):
        rides_array = self.__rides.values()
        pending_rides = filter(lambda r: not (r.get_info["request"]["state"] in [RideRequestState.CANCELED, RideRequestState.ACCEPTED]))
        pending_rides_info = map(lambda r: r.get_info())
        return pending_rides_info

    def get_ride_info(self, ride_id):
        ride = self.__rides[ride_id]
        return ride.get_info()

    def get_rides_info_by_state(self, state="all"):
        if state == "all":
            rides_info = map(lambda r: r.get_info(), self.__rides.values())
            return rides_info
        filtered_rides_info = []
        for ride in self.__rides.values():
            ride_info = ride.get_info()
            if ride_info.state == state:
                filtered_rides_info.append(ride.get_info())
        return filtered_rides_info

    def get_ride_info_by_customer_id(self, customer_id):
        filtered_rides = filter(lambda r: r.get_info()["customer_id"] == customer_id, self.__rides)
        assert filtered_rides == 1, "Provider.get_ride_info_by_customer_id - unknown number of rides associated to the same customer"
        return filtered_rides[0].get_info()

    def get_unprocessed_requests(self):
        return [
            *self.__unprocessed_requests
        ]

    def manage_pending_request(self, timestamp, ride_info, drivers_info):
        ride = self.__rides[ride_info["id"]]
        if ride_info["request"]["state"] in [RideRequestState.REJECTED, RideRequestState.UNPROCESSED]:
            self.set_ride_request_state(ride_info["id"], RideRequestState.SEARCHING_CANDIDATES)
            free_drivers_info = self.__free_drivers_info(drivers_info)
            self.__pending_customers.append(ride_info["customer_id"])
            free_drivers_ids = map(lambda d: d["id"], free_drivers_info)
            candidate = self.select_driver_candidate(ride_info, drivers_info, free_drivers_ids)
            if candidate:
                ride_info = ride.set_candidate(candidate)
                ride_info = ride.set_request_state(RideRequestState.SENT)
                return (RideRequestState.SENT, candidate["id"], None)
            else:
                if ride_info["customer_id"] in self.__pending_customers:
                    ride_info = ride.set_request_state(RideRequestState.NONE)
                    return [RideRequestState.NONE, None, ride_info["customer_id"]]
        elif ride_info["request"]["state"] == RideRequestState.SEARCHING_CANDIDATES:
            return (RideRequestState.SEARCHING_CANDIDATES, None, ride_info["customer_id"])
        elif ride_info["request"]["state"] == RideRequestState.NONE:
            self.__ride_not_accomplished(ride)
            return [RideRequestState.SEARCHING_CANDIDATES, None, ride_info["customer_id"]]
        elif ride_info["request"]["state"] in [RideRequestState.SENT, RideRequestState.WAITING]:
            current_candidate = ride_info["request"]["current_candidate"]
            assert current_candidate is not None, "Provider.manage_pending_request - candidate undefined [1]"
            if current_candidate and current_candidate["response_count_down"] == current_candidate["sent_request_back_timer"]:
                return (RideRequestState.RESPONSE, current_candidate["id"], None)
            else:
                ride.decrement_count_down_request()
                assert current_candidate is not None, "Provider.manage_pending_request - candidate undefined [2]"
                return (RideRequestState.WAITING, current_candidate["id"], None)
        elif ride_info["request"]["state"] == RideRequestState.ACCEPTED:
            return (RideRequestState.ACCEPTED, ride_info["driver_id"], None)
        return (RideRequestState.NONE, None, ride_info["customer_id"])

    def print_rides(self, timestamp):
        path = f"{os.getcwd()}/../output/rides_{timestamp}.json"
        with open(path, 'w') as outfile:
            json.dump(self.__rides, outfile)

    def print_rides_state(self, timestamp):
        for ride in self.__rides.values():
            ride_info = ride.get_info()
            path = f"{os.getcwd()}/../output/{ride_info['id']}.json"
            data = {
                **ride_info,
                "request": {
                    "state": ride_info["request"]["state"],
                    "current_candidate": ride_info["request"]["current_candidate"],
                    "driver_candidates": map(lambda r: {
                        **r,
                        "meeting_route": r["meeting_route"],
                    }, ride_info["request"]),
                },
                "routes": {
                    "meeting_route": ride_info["routes"]["meeting_route"],
                    "destination_route": ride_info["routes"]["destination_route"]
                },
                "current_timestamp": timestamp
            }
            with open(path, 'w') as outfile:
                json.dump(data, outfile)

    def process_customer_request(self, timestamp, ride_info, meeting_point, available_drivers_info):
        ride = self.__rides[ride_info["id"]]
        ride_info = ride.update_pending(timestamp)
        self.__nearby_drivers(ride_info, meeting_point, available_drivers_info)
        assert(ride_info["id"] in self.__unprocessed_requests, "Provider.process_customer_request - ride request not included in unprocessed request")
        self.__unprocessed_requests = filter(lambda r: not(r == ride_info["id"], self.__unprocessed_requests))

    def receive_request(self, ride):
        self.__rides[ride.get_info()["id"]] = ride
        self.__unprocessed_requests.append(ride.get_id())

    def ride_request_canceled(self, ride_id):
        self.__unprocessed_requests = filter(lambda r_id: not r_id == ride_id, self.__unprocessed_requests)
        ride = self.__rides[ride_id]
        return ride.request_canceled()

    def ride_request_rejected(self, ride_id, driver_id):
        ride = self.__rides[ride_id]
        return ride.request_rejected(driver_id)

    def set_ride_request_state(self, ride_id, ride_request_state):
        ride = self.__rides[ride_id]
        return ride.set_request_state(ride_request_state)

    def set_ride_state(self, ride_id, ride_state):
        ride = self.__rides[ride_id]
        return ride.set_state(ride_state)

    def update_ride_accepted(self, ride_id, driver_id, meeting_route, destination_route, stats):
        ride = self.rides[ride_id]
        return ride.update_accepted(driver_id, meeting_route, destination_route, stats)

    def update_ride_pickup(self, ride_id):
        ride = self.__rides[ride_id]
        return ride.update_pickup()

    def update_ride_on_road(self, ride_id, stats):
        ride = self.__rides[ride_id]
        return ride.update_on_road(stats)

    def update_ride_end(self, ride_id, stats):
        ride = self.__rides[ride_id]
        return ride.update_end(stats)

    def __free_drivers_info(self, drivers_info):
        free_drivers = []
        for driver_info in drivers_info.values():
            if not (driver_info["pending_request"] or driver_info["state"] in [DriverState.MOVING, DriverState.ONROAD, DriverState.PICKUP, DriverState.RESPONDING]):
                free_drivers.append(driver_info)
        return free_drivers

    def __get_rides_by_state(self, state):
        filtered_rides = []
        for ride in self.__rides.values():
            ride_info = ride.get_info()
            if ride_info["state"] == state:
                filtered_rides.append(ride)
        return filtered_rides

    def __nearby_drivers(self, ride_info, meeting_point, drivers_info):
        drivers_info_array = drivers_info.values()
        for driver_info in drivers_info_array:
            route = Map.generate_sumo_route_from_coordinates([driver_info["current_coordinates"], meeting_point])
            self.__pending_customers = filter(lambda c_id: not c_id == ride_info["customer_id"])
            expected_route_distance = Map.get_sumo_route_distance(route)
            expected_route_duration = Map.get_sumo_route_duration(route)

            if expected_route_distance <= self.__request["max_driver_distance"]:
                self.add_candidate_to_ride(ride_info["id"], {
                    "id": driver_info["id"],
                    "response_count_down": 15,
                    "meeting_route": route,
                    "send_request_back_timer": utils.random_int_from_range(0, 11),
                    "expected_distance": expected_route_distance,
                    "expected_duration": expected_route_duration
                })
        self.__rides[ride_info["id"]].sort_candidates()

    def __ride_not_accomplished(self, ride):
        return ride.set_state(RideState.NOT_ACCOMPLISHED)

    def __select_driver_candidate(self, ride_info, drivers_info, free_drivers_ids):
        drivers_candidates = ride_info["request"]["drivers_candidates"]
        for candidate in drivers_candidates:
            driver = drivers_info[candidate["id"]]
            if not driver["pending_request"]:
                if candidate and candidate["id"] in free_drivers_ids:
                    return candidate
        return None

