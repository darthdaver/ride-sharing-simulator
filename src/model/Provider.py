import json
import os

import traci

from src.model.Map import Map
from src.state.DriverState import DriverState
from src.state.CustomerState import CustomerState
from src.state.RideState import RideState
from src.state.RideRequestState import RideRequestState
from src.utils import utils
from src.state.HumanType import HumanType

class Provider:
    def __init__(self, provider_setup):
        self.__rides = {}
        self.__rides_by_state = {k.value: [] for k in RideState}
        self.__fare = provider_setup["fare"]
        self.__request = provider_setup["request"]

    def add_ride(self, ride):
        self.__rides[ride.get_id()] = ride

    def add_candidate_to_ride(self, ride_id, driver_candidate):
        self.__rides[ride_id].add_driver_candidate(driver_candidate)

    def find_ride_by_agent_id(self, agent_info, agent_type):
        assert agent_type in [HumanType.DRIVER, HumanType.CUSTOMER], f"Provider.find_ride_by_agent_id - unexpected agent type {agent_type}"
        state = None
        if agent_info["state"] in [DriverState.PICKUP, CustomerState.PICKUP]:
            state = RideState.PICKUP
        elif agent_info["state"] in [DriverState.ON_ROAD, CustomerState.ON_ROAD]:
            state = RideState.ON_ROAD
        elif agent_info["state"] in [DriverState.RESPONDING, CustomerState.PENDING]:
            state = RideState.PENDING
        else:
            assert False, f"Provider.find_ride_by_agent_id - unexpected agent state {agent_info['state']}"
        for ride_id in self.__rides_by_state[state.value]:
            ride = self.__rides[ride_id]
            ride_info = ride.get_info()
            if agent_type == HumanType.DRIVER:
                if state == RideState.PENDING:
                    if ride_info["request"]["current_candidate"]["id"] == agent_info["id"]:
                        return ride_info
                else:
                    if ride_info["driver_id"] == agent_info["id"]:
                        return ride_info
            elif agent_type == HumanType.CUSTOMER:
                if ride_info["customer_id"] == agent_info["id"]:
                    return ride_info
        return None

    def print_rides_number(self):
        print(len(self.__rides.keys()))

    def compute_price(self, travel_time, ride_length, surge_multiplier):
        base_fare = self.__fare["base_fare"]
        fee_per_minute = self.__fare["fee_per_minute"]
        fee_per_mile = self.__fare["fee_per_mile"]
        price = (base_fare + (fee_per_minute * travel_time) + (fee_per_mile * ride_length/1000)) * surge_multiplier
        return price

    def get_ride_meeting_route(self, ride_id):
        ride = self.__rides[ride_id]
        return ride.get_meeting_route()

    def get_ride_destination_route(self, ride_id):
        ride = self.__rides[ride_id]
        return ride.get_destination_route()

    def get_pending_rides(self):
        rides_array = list(self.__rides.values())
        pending_rides = list(filter(lambda r: not (r.get_info()["request"]["state"] in [RideRequestState.CANCELED, RideRequestState.ACCEPTED]), rides_array))
        pending_rides_info = list(map(lambda r: r.get_info(), pending_rides))
        return pending_rides_info

    def get_ride_info(self, ride_id):
        ride = self.__rides[ride_id]
        return ride.get_info()

    def get_rides_info_by_state(self, state="all"):
        if state == "all":
            rides_array = list(self.__rides.values())
            rides_info = list(map(lambda r: r.get_info(), rides_array))
            return rides_info
        filtered_rides_info = []
        for ride_id in self.__rides_by_state[state]:
            ride = self.__rides[ride_id]
            filtered_rides_info.append(ride.get_info())
        return filtered_rides_info

    def get_ride_info_by_customer_id(self, customer_id):
        filtered_rides = list(filter(lambda r: r.get_info()["customer_id"] == customer_id, self.__rides))
        assert filtered_rides == 1, "Provider.get_ride_info_by_customer_id - unknown number of rides associated to the same customer"
        return filtered_rides[0].get_info()

    def get_unprocessed_requests(self):
        return [
            *self.__rides_by_state[RideState.REQUESTED.value]
        ]

    def manage_pending_request(self, ride_info, drivers_info):
        ride = self.__rides[ride_info["id"]]
        if ride_info["request"]["state"] in [RideRequestState.REJECTED, RideRequestState.UNPROCESSED]:
            self.set_ride_request_state(ride_info["id"], RideRequestState.SEARCHING_CANDIDATES)
            free_drivers_info = self.__free_drivers_info(drivers_info)
            free_drivers_ids = list(map(lambda d: d["id"], free_drivers_info))
            candidate = self.__select_driver_candidate(ride_info, drivers_info, free_drivers_ids)
            if candidate:
                ride_info = ride.set_candidate(candidate)
                ride_info = ride.set_request_state(RideRequestState.SENT)
                return (ride_info, RideRequestState.SENT, candidate["id"])
            else:
                ride_info = ride.set_request_state(RideRequestState.NONE)
                return [ride_info, RideRequestState.NONE, None]
        elif ride_info["request"]["state"] == RideRequestState.SEARCHING_CANDIDATES:
            return (ride_info, RideRequestState.SEARCHING_CANDIDATES, None)
        elif ride_info["request"]["state"] == RideRequestState.NONE:
            ride_info = self.__ride_not_accomplished(ride)
            return [ride_info, RideRequestState.NONE, None]
        elif ride_info["request"]["state"] in [RideRequestState.SENT, RideRequestState.WAITING]:
            current_candidate = ride_info["request"]["current_candidate"]
            assert current_candidate is not None, "Provider.manage_pending_request - candidate undefined [1]"
            if current_candidate and current_candidate["response_count_down"] == current_candidate["send_request_back_timer"]:
                return (ride_info, RideRequestState.RESPONSE, current_candidate["id"])
            else:
                ride.decrement_count_down_request()
                assert current_candidate is not None, "Provider.manage_pending_request - candidate undefined [2]"
                return (ride_info, RideRequestState.WAITING, current_candidate["id"])
        return (ride_info, RideRequestState.NONE, None)

    def print_rides(self, timestamp):
        path = f"{os.getcwd()}/output/rides_{timestamp}.json"
        with open(path, 'a') as outfile:
            json.dump(self.__rides, outfile)

    def print_rides_state(self, timestamp):
        for ride in self.__rides.values():
            ride_info = ride.get_info()
            path = f"{os.getcwd()}/output/{ride_info['id']}.json"
            data = {
                **ride_info,
                "request": {
                    "state": ride_info["request"]["state"].value,
                    "current_candidate": {
                        **ride_info["request"]["current_candidate"],
                        "meeting_route": ride_info["request"]["current_candidate"]["meeting_route"].to_dict()
                    } if ride_info["request"]["current_candidate"] is not None else None,
                    "driver_candidates": list(map(lambda d: {
                        **d,
                        "meeting_route": d["meeting_route"].to_dict(),
                    }, ride_info["request"]["drivers_candidates"])),
                },
                "routes": {
                    "meeting_route": ride_info["routes"]["meeting_route"],
                    "destination_route": ride_info["routes"]["destination_route"]
                },
                "current_timestamp": timestamp
            }
            with open(path, 'a') as outfile:
                json.dump(data, outfile)

    def process_customer_request(self, timestamp, sumo_net, ride_info, meeting_point, available_drivers_info):
        ride = self.__rides[ride_info["id"]]
        ride_info = ride.update_pending(timestamp)
        self.__nearby_drivers(timestamp, sumo_net, ride_info, meeting_point, available_drivers_info)
        assert ride_info["id"] in self.__rides_by_state[RideState.REQUESTED.value], "Provider.process_customer_request - ride request not included in unprocessed request"
        self.__rides_by_state[RideState.REQUESTED.value].remove(ride_info["id"])
        self.__rides_by_state[RideState.PENDING.value].append(ride_info["id"])

    def receive_request(self, ride):
        ride_info = ride.get_info()
        self.__rides[ride_info["id"]] = ride
        self.__rides_by_state[RideState.REQUESTED.value].append(ride_info["id"])

    def refine_ride_route(self, ride_id, route, route_type):
        assert route_type in ["meeting_route","destination_route"], f"Provider.refine_ride_route - unexpected route_type {route_type}"
        ride = self.__rides[ride_id]
        ride_info = ride.refine_route(route_type, route)
        return ride_info

    def remove_ride_simulation_error(self, ride_id):
        ride = self.__rides[ride_id]
        ride_info = ride.get_info()
        self.__rides_by_state[ride_info["state"].value].remove(ride_id)
        ride.set_state(RideState.SIMULATION_ERROR)
        self.__rides_by_state[RideState.SIMULATION_ERROR.value].append(ride_id)

    def ride_request_canceled(self, ride_id):
        assert ride_id in self.__rides_by_state[RideState.REQUESTED.value], f"Provider.ride_request_canceled - Unexpected ride state for {ride_id}."
        self.__rides_by_state[RideState.REQUESTED.value].remove(ride_id)
        self.__rides_by_state[RideState.CANCELED.value].append(ride_id)
        ride = self.__rides[ride_id]
        return ride.request_canceled()

    def ride_request_rejected(self, ride_id, driver_id):
        ride = self.__rides[ride_id]
        ride_info = ride.get_info()
        assert ride_info["state"] == RideState.PENDING, f"Unexpected ride state {ride_info['state']} for {ride_id}"
        return ride.request_rejected(driver_id)

    def set_ride_request_state(self, ride_id, ride_request_state):
        ride = self.__rides[ride_id]
        return ride.set_request_state(ride_request_state)

    def set_ride_state(self, ride_id, ride_state):
        ride = self.__rides[ride_id]
        ride_info = ride.get_info()
        self.__rides_by_state[ride_info["state"].value].remove(ride_id)
        self.__rides_by_state[ride_state].append(ride_id)
        return ride.set_state(ride_state)

    def update_ride_accepted(self, ride_id, driver_id, meeting_route, destination_route, stats):
        ride = self.__rides[ride_id]
        ride_info = ride.get_info()
        self.set_ride_request_state(ride_info["id"], RideRequestState.ACCEPTED)
        return ride.update_accepted(driver_id, meeting_route, destination_route, stats)

    def update_ride_pickup(self, ride_id):
        ride = self.__rides[ride_id]
        ride_info = ride.get_info()
        assert ride_info["state"] == RideState.PENDING, f"Provider.update_ride_pickup - unexpected ride state {ride_info['state']} for {ride_id}"
        self.__rides_by_state[RideState.PENDING.value].remove(ride_id)
        self.__rides_by_state[RideState.PICKUP.value].append(ride_id)
        return ride.update_pickup()

    def update_ride_on_road(self, ride_id, stats):
        ride = self.__rides[ride_id]
        ride_info = ride.get_info()
        assert ride_info["state"] == RideState.PICKUP, f"Provider.update_ride_pickup - unexpected ride state {ride_info['state']} for {ride_id}"
        self.__rides_by_state[RideState.PICKUP.value].remove(ride_id)
        self.__rides_by_state[RideState.ON_ROAD.value].append(ride_id)
        return ride.update_on_road(stats)

    def update_ride_end(self, ride_id, stats):
        ride = self.__rides[ride_id]
        ride_info = ride.get_info()
        assert ride_info["state"] == RideState.ON_ROAD, f"Provider.update_ride_pickup - unexpected ride state {ride_info['state']} for {ride_id}"
        self.__rides_by_state[RideState.ON_ROAD.value].remove(ride_id)
        self.__rides_by_state[RideState.END.value].append(ride_id)
        return ride.update_end(stats)

    def __free_drivers_info(self, drivers_info):
        free_drivers = []
        for driver_info in drivers_info.values():
            if driver_info["id"] in traci.vehicle.getIDList():
                free_drivers.append(driver_info)
        return free_drivers

    def __get_rides_by_state(self, states):
        states = map(lambda s: s.value, states)
        filtered_rides = []
        for state, rides_ids_by_state in self.__rides_by_state.items():
            if state in states:
                filtered_rides.extend(rides_ids_by_state)
        return filtered_rides

    def __nearby_drivers(self, timestamp, sumo_net, ride_info, meeting_point, drivers_info):
        drivers_info_array = list(drivers_info.values())
        for driver_info in drivers_info_array:
            driver_id = driver_info["id"]
            try:
                print(f"Map.__nearby_drivers | Driver {driver_info['id']} - generate route from {driver_info['current_coordinates']} to destination {meeting_point}")
                route = Map.generate_route_from_coordinates(timestamp, sumo_net, [driver_info["current_coordinates"], meeting_point])
                expected_route_distance = route.get_original_distance()
                expected_route_duration = route.get_original_duration()

                if expected_route_distance <= self.__request["max_driver_distance"]:
                    self.add_candidate_to_ride(ride_info["id"], {
                        "id": driver_id,
                        "response_count_down": 15,
                        "meeting_route": route,
                        "send_request_back_timer": utils.random_int_from_range(0, 11),
                        "expected_distance": expected_route_distance,
                        "expected_duration": expected_route_duration
                    })
            except:
                print(f"Provider.__nearby_drivers - Impossbile to generate route for driver {driver_info['id']}")
                continue
        self.__rides[ride_info["id"]].sort_candidates()

    def __ride_not_accomplished(self, ride):
        ride_info = ride.get_info()
        self.__rides_by_state[ride_info["state"].value].remove(ride_info["id"])
        self.__rides_by_state[RideState.NOT_ACCOMPLISHED.value].append(ride_info["id"])
        return ride.set_state(RideState.NOT_ACCOMPLISHED)

    def __select_driver_candidate(self, ride_info, drivers_info, free_drivers_ids):
        drivers_candidates = ride_info["request"]["drivers_candidates"]
        for candidate in drivers_candidates:
            if candidate and candidate["id"] in free_drivers_ids:
                return candidate
        return None

