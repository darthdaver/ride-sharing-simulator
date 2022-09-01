import math
import random

from src.state.FileSetup import FileSetup
from src.state.CustomerState import CustomerState
from src.state.DriverState import DriverState
from src.state.RideState import RideState
from src.state.RideRequestState import RideRequestState
from src.state.HumanPersonality import HumanPersonality
from src.state.EventType import EventType
from src.state.HumanType import HumanType
from src.utils import utils
from src.model.Scenario import Scenario
from src.model.Provider import Provider
from src.model.Map import Map
from src.model.Ride import Ride
from src.model.Customer import Customer
from src.model.Driver import Driver
from src.model.EnergyIndexes import EnergyIndexes
from src.model.Route import Route
from src.model.Printer import Printer
from src.settings.Settings import Settings
import os
import traci
from traci import tc
import sumolib
import sys

env_settings = Settings()

H3_RESOLUTION = env_settings.H3_RESOLUTION

class Simulator:
    def __init__(self):
        self.__customer_setup = utils.read_setup(FileSetup.CUSTOMER.value)
        self.__driver_setup = utils.read_setup(FileSetup.DRIVER.value)
        self.__simulator_setup = utils.read_setup(FileSetup.SIMULATOR.value)
        self.__scenario = Scenario(utils.read_setup(FileSetup.SCENARIO.value))
        self.__provider = Provider(utils.read_setup(FileSetup.PROVIDER.value))
        self.__map = Map(utils.read_setup(FileSetup.MAP.value), H3_RESOLUTION)
        self.__sumo_net = sumolib.net.readNet(FileSetup.NET)
        self.__driver_id_counter = 0
        self.__customer_id_counter = 0
        self.__ride_id_counter = 0
        self.__traffic_counter = 0
        self.__sim_drivers_ids = []
        self.__sim_customers_ids = []
        self.__drivers = {}
        self.__customers = {}
        self.__drivers_by_state = {k.value: [] for k in DriverState}
        self.__customers_by_state = {k.value: [] for k in CustomerState}
        self.__printer = Printer()
        self.__temp_drivers_gen = 0
        self.__temp_customers_gen = 0
        self.__energy_indexes = EnergyIndexes()
        self.__timeline_generation = utils.read_setup(FileSetup.TIMELINE_GENERATION.value)
        self.__scenario = Scenario(utils.read_setup(FileSetup.SCENARIO.value))
        self.__taz_edges = utils.read_setup(FileSetup.TAZ_EDGES.value)

    def check_area_id(self, agent_info, area_id, type):
        hexagon_id = self.__map.get_hexagon_id_from_coordinates(agent_info["current_coordinates"])
        if type == "driver":
            if area_id == "unknown":
                near_hexagon = self.__map.find_near_hexagon(hexagon_id)
                if near_hexagon is not None:
                    driver = self.__drivers[agent_info["id"]]
                    return self.__map.get_area_from_hexagon(near_hexagon)
                else:
                    raise Exception(f"Unknown area id ({agent_info['current_coordinates']}) for driver {agent_info['id']} in state {agent_info['state']} not busy - 1")
            return area_id
        else:
            if area_id == "unknown":
                near_hexagon = self.__map.find_near_hexagon(hexagon_id)
                if near_hexagon is not None:
                    customer = self.__customers[agent_info["id"]]
                    return self.__map.get_area_from_hexagon(near_hexagon)
                else:
                    raise Exception(f"Unknown area id ({agent_info['current_coordinates']}) for customer {agent_info['id']} in state {agent_info['state']} not busy [1]")
            return area_id

    def __check_customers_list(self, timestamp):
        current_customers_list = traci.person.getIDList()
        if not set(current_customers_list) == set(self.__sim_customers_ids):
            customers_diff = list(set(self.__sim_customers_ids).symmetric_difference(set(current_customers_list)))
            for customer_id in customers_diff:
                if not customer_id in current_customers_list:
                    customer_info = self.__customers[customer_id].get_info()
                    customer_area_id = self.check_area_id(customer_info, self.__map.get_area_from_coordinates(customer_info["current_coordinates"]), "customer")
                    if not customer_area_id == "unknown":
                        self.__generate_customer(timestamp, customer_area_id)
                    self.__remove_customer_by_state(customer_id)
                elif not customer_id in self.__sim_customers_ids:
                    traci.person.remove(customer_id)

    def __check_drivers_list(self, timestamp):
        current_drivers_list = traci.vehicle.getIDList()
        if not set(current_drivers_list) == set(self.__sim_drivers_ids):
            drivers_diff = list(set(self.__sim_drivers_ids).symmetric_difference(set(current_drivers_list)))
            for driver_id in drivers_diff:
                if not driver_id in current_drivers_list:
                    driver_info = self.__drivers[driver_id].get_info()
                    driver_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(driver_info["current_coordinates"]), "driver")
                    if not driver_area_id == "unknown":
                        self.__generate_driver(timestamp, driver_area_id, last_ride_timestamp=driver_info["last_ride_timestamp"], rides_completed=driver_info["rides_completed"])
                    print(12)
                    self.__remove_driver_by_state(driver_id)
                elif not driver_id in self.__sim_drivers_ids:
                    traci.vehicle.remove(driver_id)

    def __generate_agent_id(self, agent_type):
        assert agent_type in [HumanType.DRIVER, HumanType.CUSTOMER], "Simulator.generateAgentId - unknown agentType"
        counter = 0
        if agent_type == HumanType.CUSTOMER:
            counter = self.__customer_id_counter
            self.__customer_id_counter += 1
        else:
            counter = self.__driver_id_counter
            self.__driver_id_counter += 1
        return f"{agent_type.value.lower()}_{counter}"

    def __generate_customer(self, timestamp, area_id, hexagon_id="random"):
        area_info = self.__map.get_area_info(area_id)
        coordinates = self.__map.generate_random_coordinates_from_hexagon(self.__sumo_net, area_id, hexagon_id)
        customer_personality_distribution = area_info["personality_policy"]["customer"]
        customer_id = self.__generate_agent_id(HumanType.CUSTOMER)
        customer = Customer(timestamp, customer_id, CustomerState.ACTIVE, customer_personality_distribution, coordinates)
        self.__customers[customer_id] = customer
        self.__customers_by_state[CustomerState.ACTIVE.value].append(customer_id)
        edge_id = Map.get_sumo_edge_id_from_coordinates(self.__sumo_net, coordinates)
        pos = Map.get_sumo_lane_position_from_coordinates(self.__sumo_net, coordinates)
        traci.person.add(customer_id, edge_id, pos, depart=timestamp)
        traci.person.appendWaitingStage(customer_id, 1000)
        self.__sim_customers_ids.append(customer_id)
        #print(f"Generated {customer_id}")

    def __generate_customer_requests(self, timestamp):
        for customer_id in self.__customers_by_state[CustomerState.ACTIVE.value]:
            ride_id = f"ride_{self.__ride_id_counter}"
            self.__ride_id_counter += 1
            meeting_coordinates = self.__customers[customer_id].get_info()["current_coordinates"]
            route_length = utils.select_from_distribution(self.__customer_setup["route_length_distribution"])
            destination_coordinates = self.__map.generate_destination_point(self.__sumo_net, meeting_coordinates, route_length)
            source_area_id = self.__map.get_area_from_coordinates(meeting_coordinates)
            try:
                destination_area_id = self.__map.get_area_from_coordinates(destination_coordinates)

                stats = {
                    "source_area_id": source_area_id,
                    "destination_area_id": destination_area_id
                }

                ride = Ride(ride_id, customer_id, meeting_coordinates, destination_coordinates, stats)
                self.__provider.receive_request(ride)
                self.__energy_indexes.received_request(timestamp)
            except:
                #self.__customers_by_state[CustomerState.ACTIVE.value].remove(customer_id)
                #self.__customers_by_state[CustomerState.INACTIVE.value].append(customer_id)
                self.__remove_customer(customer_id)
                continue

    def __generate_driver(self, timestamp, area_id, hexagon_id="random", last_ride_timestamp=None, rides_completed=0):
        area_info = self.__map.get_area_info(area_id)
        coordinates = self.__map.generate_random_coordinates_from_hexagon(self.__sumo_net, area_id, hexagon_id)
        driver_personality_distribution = area_info["personality_policy"]["driver"]
        driver_id = self.__generate_agent_id(HumanType.DRIVER)
        try:
            #print(f"Simulator.__generate_driver | Driver {driver_id} - generate random route")
            random_route = self.__map.generate_random_route_in_area(timestamp, self.__sumo_net, coordinates)
            traci.vehicle.add(driver_id, random_route.get_route_id())
            traci.vehicle.setRoutingMode(driver_id,tc.ROUTING_MODE_AGGREGATED)
            driver = Driver(timestamp, driver_id, DriverState.IDLE, driver_personality_distribution, coordinates, random_route, last_ride_timestamp=last_ride_timestamp, rides_completed=rides_completed)
            self.__drivers[driver_id] = driver
            self.__drivers_by_state[DriverState.IDLE.value].append(driver_id)
            self.__sim_drivers_ids.append(driver_id)
            #print(f"Generated {driver_id}")
        except:
            print(f"Simulator.__generate_driver - Impossible to find route. Driver {driver_id} not generated.")

    def __generate_traffic(self, timestamp, area_id, num_drivers, hexagon_id="random"):
        for i in range(num_drivers):
            vehicle_id = f"vehicle_{self.__traffic_counter}"
            self.__traffic_counter += 1
            try:
                coordinates = self.__map.generate_random_coordinates_from_hexagon(self.__sumo_net, area_id, hexagon_id)
                route_length = utils.select_from_distribution(self.__customer_setup["route_length_distribution"])
                destination_coordinates = self.__map.generate_destination_point(self.__sumo_net, coordinates, route_length)
                route = Map.generate_route_from_coordinates(timestamp, self.__sumo_net, [coordinates, destination_coordinates])
                traci.vehicle.add(vehicle_id, route.get_route_id())
            except:
                print(f"Simulator.__generate_traffic - Impossible to find route. Vehicle {vehicle_id} not generated.")

    def __get_available_drivers(self, area_id):
        idle_drivers = self.__get_drivers_info_by_states([DriverState.IDLE])
        drivers_moving_in_area = self.__get_drivers_info_moving_in_area(area_id)
        available_drivers = {
            **idle_drivers,
            **drivers_moving_in_area
        }
        return available_drivers

    def __get_customers_in_area(self, area_id):
        customers_in_area = {}
        customers_snapshot = [*self.__customers.values()]
        for customer in customers_snapshot:
            customer_info = customer.get_info()
            if not customer_info["state"] == CustomerState.INACTIVE:
                customer_area_id = self.check_area_id(customer_info, self.__map.get_area_from_coordinates(customer_info["current_coordinates"]), "customer")
                if customer_area_id == "unknown":
                    self.__remove_customer_by_state(customer_info["id"])
                    continue
                if area_id == customer_area_id:
                    customers_in_area[customer_info["id"]] = customer_info
        return customers_in_area

    def __get_drivers_in_area(self, area_id):
        drivers_in_area = {}
        drivers_snapshot = [*self.__drivers.values()]
        for driver in drivers_snapshot:
            driver_info = driver.get_info()
            if not driver_info["state"] == DriverState.INACTIVE:
                driver_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(driver_info["current_coordinates"]), "driver")
                if driver_area_id == "unknown":
                    print(13)
                    self.__remove_driver_by_state(driver_info["id"])
                    continue
                if area_id == driver_area_id:
                    drivers_in_area[driver_info["id"]] = driver_info
        return drivers_in_area

    def __get_drivers_info_moving_in_area(self, area_id):
        drivers_moving_in_area = {}
        for driver_id in self.__drivers_by_state[DriverState.MOVING.value]:
            driver_info = self.__drivers[driver_id].get_info()
            assert driver_info["route"] is not None, "Simulator.__get_drivers_info_moving_in_area - driver route not found"
            destination_coordinates = driver_info["route"]["destination_point"]
            destination_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(destination_coordinates), 'driver')
            if destination_area_id == "unknown":
                print(14)
                self.__remove_driver_by_state(driver_info["id"])
                continue
            if area_id == destination_area_id:
                drivers_moving_in_area[driver_info["id"]] = driver_info
        return drivers_moving_in_area

    def __get_drivers_info(self):
        drivers_info = {}
        for driver_id, driver in self.__drivers.items():
            drivers_info[driver_id] = driver.get_info()
        return drivers_info

    def __get_drivers_info_by_states(self, states):
        states = list(map(lambda s: s.value, states))
        drivers_info = {}
        for state, drivers_ids_by_state in self.__drivers_by_state.items():
            if state in states:
                for driver_id in drivers_ids_by_state:
                    driver = self.__drivers[driver_id]
                    driver_info = driver.get_info()
                    drivers_info[driver_id] = driver_info
        return drivers_info

    def __get_human_policy(self, policy, personality):
        assert personality in [HumanPersonality.HURRY.value, HumanPersonality.NORMAL.value, HumanPersonality.GREEDY.value], f"Simulator.__get_human_policy - Unknown personality: {personality}"
        return policy[personality.lower()]

    def __is_driver_still_active(self, driver_id):
        driver = self.__drivers[driver_id]
        driver_info = driver.get_info()
        return not driver_info["state"] == DriverState.INACTIVE

    def __manage_pending_request(self, timestamp):
        pending_requests = self.__provider.get_rides_info_by_state(RideState.PENDING.value)
        for ride_info in pending_requests:
            driver_acceptance_policy = self.__driver_setup["driver_acceptance_policy"]
            customer_info = self.__customers[ride_info["customer_id"]].get_info()
            area_id = self.check_area_id(customer_info, self.__map.get_area_from_coordinates(ride_info["meeting_point"]), 'customer')
            #assert (not area_id == 'unknown') and type(area_id) is str, f"Simulator.__manage_pending_request - Unexpected unknown id area ({customer_info['current_coordinates']}) for customer {ride_info['customer_id']}."
            if area_id == "unknown":
                self.__remove_customer_by_state(customer_id)
                self.__provider.remove_ride_simulation_error(ride_info["id"])
                continue
            area_info = self.__map.get_area_info(area_id)
            surge_multiplier = area_info["surge_multipliers"][0]
            available_drivers_info = self.__get_available_drivers(area_id)
            ride_info, ride_request_state, driver_id = self.__provider.manage_pending_request(ride_info, available_drivers_info)
            customer_id = ride_info["customer_id"]
            if ride_request_state == RideRequestState.SENT:
                assert not driver_id == None, "Simulator.__manage_pending_request - Unexpected driver id None."
                drivers_info = self.__send_request_to_driver(driver_id)
                self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.SENT)
            elif ride_request_state == RideRequestState.WAITING:
                assert driver_id is not None, "Simulator.__manage_pending_request - Unexpected undefined driver id when request state has been sent. [1]"
                if not self.__is_driver_still_active(driver_id):
                    assert driver_id in self.__drivers_by_state[DriverState.INACTIVE.value], f"Simulator.__manage_pending_request - unexpected driver state for {driver_id}"
                    ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
                    ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
            elif ride_request_state == RideRequestState.RESPONSE:
                assert driver_id is not None, "Simulator.__manage_pending_request - Unexpected undefined driver id when request state has been sent. [2]"
                if not self.__is_driver_still_active(driver_id):
                    ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
                    ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
                driver = self.__drivers[driver_id]
                driver_info = driver.get_info()
                personality = driver_info["personality"]
                driver_policy = self.__get_human_policy(driver_acceptance_policy, personality)
                accept = driver.accept_ride_conditions(surge_multiplier, driver_policy)
                if accept:
                    try:
                        meeting_route = Map.generate_route_from_agents(timestamp, driver_info, HumanType.DRIVER, customer_info, HumanType.CUSTOMER)
                        destination_route = Map.generate_route_from_agent_to_destination_point(timestamp, self.__sumo_net, customer_info, HumanType.CUSTOMER, ride_info["destination_point"])
                    except:
                        driver_info = driver.reject_request()
                        assert driver_id in self.__drivers_by_state[DriverState.RESPONDING.value], f"Simulator.__manage_pending_request - unexpected driver state for {driver_id}"
                        self.__drivers_by_state[DriverState.RESPONDING.value].remove(driver_id)
                        self.__drivers_by_state[DriverState.IDLE.value].append(driver_id)
                        ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
                        ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
                        break
                    assert ride_info["request"]["current_candidate"] is not None, "Simulator.__manage_pending_request - candidate undefined on ride request response"
                    customer = self.__customers[customer_id]
                    expected_ride_duration = destination_route.get_original_duration()
                    expected_ride_length = destination_route.get_original_distance()
                    expected_price = self.__provider.compute_price(expected_ride_duration, expected_ride_length, surge_multiplier)
                    stats = {
                        "timestamp_pickup": timestamp,
                        "expected_meeting_length": meeting_route.get_original_distance(),
                        "expected_meeting_duration": meeting_route.get_original_duration(),
                        "expected_price": expected_price,
                        "expected_ride_duration": expected_ride_duration,
                        "expected_ride_length": expected_ride_length,
                        "surge_multiplier": surge_multiplier
                    }
                    customer_info = customer.update_pickup()
                    driver_info = driver.update_pickup(meeting_route)
                    self.__drivers_by_state[DriverState.RESPONDING.value].remove(driver_id)
                    self.__drivers_by_state[DriverState.PICKUP.value].append(driver_id)
                    self.__customers_by_state[CustomerState.PENDING.value].remove(customer_id)
                    self.__customers_by_state[CustomerState.PICKUP.value].append(customer_id)
                    try:
                        self.__start_sumo_route(timestamp, driver_id, customer_id, ride_info["id"])
                        ride_info = self.__provider.update_ride_accepted(ride_info["id"], driver_id, meeting_route, destination_route, stats)
                        driver_info = driver.set_current_distance((math.inf, math.inf))
                        self.__provider.update_ride_pickup(ride_info["id"])
                        self.__printer.save_ride_assignation(timestamp, ride_info["id"], customer_info["id"], driver_id)
                        self.__energy_indexes.accepted_request(timestamp)
                    except:
                        print("Simulator.__manage_pending_request - Impossible to start sumo route")
                        self.__customers_by_state[CustomerState.PICKUP.value].remove(customer_id)
                        self.__customers_by_state[CustomerState.PENDING.value].append(customer_id)
                        customer_info = customer.set_state(CustomerState.PENDING)
                        ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
                        ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
                        break
                else:
                    driver_info = driver.reject_request()
                    self.__drivers_by_state[DriverState.RESPONDING.value].remove(driver_id)
                    self.__drivers_by_state[DriverState.IDLE.value].append(driver_id)
                    ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
                    ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
            elif ride_request_state in [RideRequestState.NONE, RideRequestState.ROUTE_NOT_FOUND]:
                assert customer_id is not None, "Simulator.managePendingRequest - id customer undefined on ride request not accomplished."
                self.__remove_customer(customer_id)
                if ride_request_state == RideRequestState.NONE:
                    self.__energy_indexes.request_not_accomplished(timestamp)

    def __map_pending_request_area(self, r):
        customer_info = self.__customers[r["customer_id"]].get_info()
        coordinates_request = customer_info["current_coordinates"]
        area_request_id = self.__map.get_area_from_coordinates(coordinates_request)
        return {
            **r,
            "area_request_id": area_request_id
        }

    def __move_driver_to_area(self, timestamp, driver_id, area_id):
        try:
            self.__start_sumo_route(timestamp, driver_id, area_id)
            self.__drivers_by_state[DriverState.IDLE.value].remove(driver_id)
            self.__drivers_by_state[DriverState.MOVING.value].append(driver_id)
            print(f"Move driver {driver_id} to area {area_id}")
        except:
            driver_info = self.__drivers[driver_id].get_info()
            driver_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(driver_info["current_coordinates"]), "driver")
            if not driver_area_id == "unknown":
                self.__generate_driver(timestamp, driver_area_id, last_ride_timestamp=driver_info["last_ride_timestamp"], rides_completed=driver_info["rides_completed"])
            print(15)
            self.__remove_driver(driver_id)
            print(f"Impossible to move driver {driver_id} to area {area_id}")

    def __perform_scenario_event(self, timestamp, event_type, params):
        if event_type == EventType.HUMAN_PERSONALITY_POLICY:
            assert params["agent_type"] in [HumanType.DRIVER.value.lower(), HumanType.CUSTOMER.value.lower()], f"Map.update_personality_policy - unknown label {params['agent_type']}"
            areas = params["areas"] if not params["areas"] == [] else self.__map.get_area_ids()
            agent_type = HumanType.DRIVER if params["agent_type"] == HumanType.DRIVER.value.lower() else HumanType.CUSTOMER
            for area_id in areas:
                area_info = self.__map.get_area_info(area_id)
                if int(timestamp) == params["start"]:
                    self.__map.update_personality_policy(area_id, params["initial_human_personality_policy"], agent_type)
                if params["operation"] == "increment":
                    area_personality_policy = area_info["personality_policy"][agent_type.value.lower()]
                    new_personality_policy = []
                    for v, human_personality in area_personality_policy:
                        new_personality_policy.append([round(params["value"][human_personality] + v, 4), human_personality])
                    self.__map.update_personality_policy(area_id, new_personality_policy, agent_type)
                    #print(f"new personality policy: {new_personality_policy} - area_id: {area_id}")
        if event_type == EventType.INCREASE_LENGTH_RIDES:
            if int(timestamp) == params["start"]:
                self.__customer_setup["route_length_distribution"] = params["initial_route_length_distribution"]
            if params["operation"] == "increment":
                route_length_distribution = self.__customer_setup["route_length_distribution"]
                new_route_length_distribution = []
                for p, length in route_length_distribution:
                    new_route_length_distribution.append([round(p + params["value"][str(length)], 4), length])
                self.__customer_setup["route_length_distribution"] = new_route_length_distribution
                print(f"new length distribution: {new_route_length_distribution}")
        if event_type == EventType.GENERATE_TRAFFIC:
            areas = params["areas"] if not params["areas"] == [] else self.__map.get_area_ids()
            for area_id in areas:
                if params["operation"] == "increment":
                    num_drivers = params["value"]
                    self.__generate_traffic(timestamp, area_id, num_drivers)
        if event_type == EventType.DRIVERS_STRIKE:
            for driver_id in [*self.__drivers_by_state[DriverState.IDLE.value], *self.__drivers_by_state[DriverState.MOVING.value]]:
                driver_info = self.__drivers[driver_id].get_info()
                if driver_info["personality"] == HumanPersonality.GREEDY.value:
                    if utils.random_choice(params["value"]["GREEDY"]):
                        #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                        self.__remove_driver(driver_id)
                elif driver_info["personality"] == HumanPersonality.NORMAL.value:
                    if utils.random_choice(params["value"]["NORMAL"]):
                        #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                        self.__remove_driver(driver_id)
                elif driver_info["personality"] == HumanPersonality.HURRY.value:
                    if utils.random_choice(params["value"]["HURRY"]):
                        #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                        self.__remove_driver(driver_id)
        if event_type == EventType.BEHAVIOR_CHANGE:
            for driver_id in [*self.__drivers_by_state[DriverState.IDLE.value], *self.__drivers_by_state[DriverState.MOVING.value]]:
                driver = self.__drivers[driver_id]
                driver_info = self.__drivers[driver_id].get_info()
                if driver_info["personality"] == HumanPersonality.GREEDY.value:
                    if not params["value"]["GREEDY"]["NORMAL"] is None:
                        if utils.random_choice(params["value"]["GREEDY"]["NORMAL"]):
                            #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                            driver_info = driver.change_personality(HumanPersonality.NORMAL.value)
                    if not params["value"]["GREEDY"]["HURRY"] is None:
                        if utils.random_choice(params["value"]["GREEDY"]["HURRY"]):
                            #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                            driver_info = driver.change_personality(HumanPersonality.HURRY.value)
                elif driver_info["personality"] == HumanPersonality.NORMAL.value:
                    if not params["value"]["NORMAL"]["GREEDY"] is None:
                        if utils.random_choice(params["value"]["NORMAL"]["GREEDY"]):
                            #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                            driver_info = driver.change_personality(HumanPersonality.GREEDY.value)
                    if not params["value"]["NORMAL"]["HURRY"] is None:
                        if utils.random_choice(params["value"]["NORMAL"]["HURRY"]):
                            #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                            driver_info = driver.change_personality(HumanPersonality.HURRY.value)
                elif driver_info["personality"] == HumanPersonality.HURRY.value:
                    if not params["value"]["HURRY"]["GREEDY"] is None:
                        if utils.random_choice(params["value"]["HURRY"]["GREEDY"]):
                            #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                            driver_info = driver.change_personality(HumanPersonality.GREEDY.value)
                    if not params["value"]["HURRY"]["NORMAL"] is None:
                        if utils.random_choice(params["value"]["HURRY"]["NORMAL"]):
                            #print(f"{driver_id} with personality {driver_info['personality']} joined the strike")
                            driver_info = driver.change_personality(HumanPersonality.NORMAL.value)
        if event_type == EventType.FLASH_MOB:
            timestamp = int(timestamp)
            if timestamp <= params["end_slow_down"]:
                if timestamp in params["flash_mob_areas"]:
                    flash_areas = params["flash_mob_areas"][f"{timestamp}"]
                    for area_id in flash_areas:
                        if area_id in self.__taz_edges:
                            edges = self.__taz_edges[area_id]
                            for edge_id in edges:
                                edge = self.__sumo_net.getEdge(edge_id)
                                edge_speed = edge.getSpeed()
                                traci.edge.setMaxSpeed(edge_id, edge_speed * (1 - params["slow_down_percentage"]))
            else:
                delta_timestamp_restore = timestamp - params["end_slow_down"]
                flash_areas = params["flash_mob_areas"]
                flash_areas_list = [area for areas in flash_areas.values() for area in areas]
                for area_id in flash_areas_list:
                    if area_id in self.__taz_edges:
                        edges = self.__taz_edges[area_id]
                        for edge_id in edges:
                            edge = self.__sumo_net.getEdge(edge_id)
                            edge_speed = edge.getSpeed()
                            speed_factor = 1 - (params["slow_down_percentage"] - (params["increase_rate"] * delta_timestamp_restore))
                            assert speed_factor >= 0, f"Simulator.__perform_scenario_event - speed factor is negative: 1 - ({params['slow_down_percentage']} - ({params['increase_rate']} * {delta_timestamp_restore}))"
                            traci.edge.setMaxSpeed(edge_id, edge_speed * speed_factor)
        if event_type == EventType.SUDDEN_REQUESTS:
            timestamp = int(timestamp)
            for area_id, request_timestamps in params["areas"]:
                occurences = request_timestamps.count(timestamp)
                for i in range(occurences):
                    self.__generate_customer(timestamp, f"{area_id}")


    def __populate_scenario(self):
        for area_id, area_info in self.__map.get_areas_info().items():
            for i in range(1):
                if utils.random_choice(0.1):
                    self.__generate_customer(0.0, area_id)
            for i in range(2):
                if utils.random_choice(0.1):
                    self.__generate_driver(0.0, area_id)

    def __process_rides(self, timestamp):
        unprocessed_requests = self.__provider.get_unprocessed_requests()

        for ride_id in unprocessed_requests:
            ride_info = self.__provider.get_ride_info(ride_id)
            customer = self.__customers[ride_info["customer_id"]]
            customer_info = customer.get_info()
            customer_acceptance_policy = self.__customer_setup["customer_acceptance_policy"]
            personality = customer.get_info()["personality"]
            area_id = self.check_area_id(customer_info, self.__map.get_area_from_coordinates(customer_info["current_coordinates"]), "customer")
            #assert (not area_id == 'unknown') and type(area_id) == str, f"Simulator.process_rides - Unexpected unknown id area ({customer_info['current_coordinates']}) fo customer {ride_info['customer_id']}"
            if area_id == "unknown":
                self.__remove_customer_by_state(customer_info['id'])
                self.__provider.remove_ride_simulation_error(ride_info["id"])
                continue
            area_info = self.__map.get_area_info(area_id)
            surge_multiplier = area_info["surge_multipliers"][0]
            customer_policy = self.__get_human_policy(customer_acceptance_policy, personality)
            accept = customer.accept_ride_conditions(surge_multiplier, customer_policy)

            if accept:
                customer_info = customer.update_pending()
                available_drivers_info = self.__get_available_drivers(area_id)
                self.__provider.process_customer_request(timestamp, self.__sumo_net, ride_info, customer_info["current_coordinates"], available_drivers_info)
                self.__customers_by_state[CustomerState.ACTIVE.value].remove(customer_info["id"])
                self.__customers_by_state[CustomerState.PENDING.value].append(customer_info["id"])
            else:
                self.__remove_customer(customer_info["id"])
                ride_info = self.__provider.ride_request_canceled(ride_id)
                self.__energy_indexes.canceled_request(timestamp)

    def random_agent_generation(self, timestamp):
        for area_id, area_info in self.__map.get_areas_info().items():
            customer_generation_probability = area_info["current_generation_probability"]["customer"][0]
            if utils.random_choice(customer_generation_probability):
                print(f"Generated customer with generation prob: {customer_generation_probability} - {area_id}")
                self.__temp_customers_gen += 1
                print(self.__temp_customers_gen)
                self.__generate_customer(timestamp, area_id)
                print(area_info["current_generation_probability"])
                self.__map.reset_agent_generation_policy(area_id, HumanType.CUSTOMER)
                print(area_info["current_generation_probability"])
            else:
                self.__map.increment_generation_probability(area_id, HumanType.CUSTOMER)
        for area_id, area_info in self.__map.get_areas_info().items():
            driver_generation_probability = area_info["current_generation_probability"]["driver"][0]
            if utils.random_choice(driver_generation_probability):
                print(f"Generated driver with generation prob: {driver_generation_probability} - {area_id}")
                self.__temp_drivers_gen += 1
                print(self.__temp_drivers_gen)
                self.__generate_driver(timestamp, area_id)
                print(area_info["current_generation_probability"])
                self.__map.reset_agent_generation_policy(area_id, HumanType.DRIVER)
                print(area_info["current_generation_probability"])
            else:
                self.__map.increment_generation_probability(area_id, HumanType.DRIVER)

    def __refine_ride_route(self, timestamp, driver_id, ride_id, route, route_type):
        try:
            driver_current_edge_id = traci.vehicle.getRoute(driver_id)[traci.vehicle.getRouteIndex(driver_id)]
        except:
            print(f"Simulator.__refine_ride_route - {driver_id} not found.")
            raise Exception(f"Simulator.__refine_ride_route - {driver_id} not found.")
        route_destination_point = route.get_destination_point()
        route_start_edge_id = route.get_route()[0]
        route_end_edge_id = route.get_route()[-1]
        driver_current_coordinates = self.__drivers[driver_id].get_info()["current_coordinates"]
        driver_current_edge = self.__sumo_net.getEdge(driver_current_edge_id)
        outgoings_driver_current_edge_ids = list(map(lambda e: e.getID(), driver_current_edge.getOutgoing()))
        assert route_start_edge_id in outgoings_driver_current_edge_ids, f"Simulator.__refine_route - unexpected {driver_id} position with respect to destination route."
        try:
            refined_route = Map.refine_sumo_route(timestamp, driver_current_edge_id, route_end_edge_id, driver_current_coordinates, route_destination_point)
            ride_info = self.__provider.refine_ride_route(ride_id, refined_route, route_type)
            return (ride_info, refined_route)
        except:
            raise Exception(f"Simulator.__refine_route - cannot find route for {driver_id} from {driver_current_edge_id} to {route_end_edge_id}")

    def __remove_customer(self, customer_id):
        print(f"Remove {customer_id}")
        customer = self.__customers[customer_id]
        customer_info = customer.get_info()
        if not customer_id in self.__customers_by_state[customer_info["state"].value]:
            print(f"{customer_id} with state {customer_info['state']}")
        self.__customers_by_state[customer_info["state"].value].remove(customer_id)
        self.__customers_by_state[CustomerState.INACTIVE.value].append(customer_id)
        customer.set_state(CustomerState.INACTIVE)
        self.__sim_customers_ids.remove(customer_id)
        if customer_id in traci.person.getIDList():
            traci.person.remove(customer_id)
        else:
            print(f"Person {customer_id} already removed...")

    def __remove_customer_by_state(self, customer_id):
        #print(f"{customer_id} disappeared from the simulation")
        customer = self.__customers[customer_id]
        customer_info = customer.get_info()
        #print(f"{customer_id} state: {customer_info['state']}")

        if customer_info["state"] in [CustomerState.ACTIVE, CustomerState.PENDING]:
            ride_info = self.__provider.find_ride_by_agent_id(customer_info, HumanType.CUSTOMER)
            if ride_info is not None:
                ride_info = self.__provider.remove_ride_simulation_error(ride_info["id"])
            self.__remove_customer(customer_id)
        elif customer_info["state"] in [CustomerState.PICKUP, CustomerState.ON_ROAD]:
            ride_info = self.__provider.find_ride_by_agent_id(customer_info, HumanType.CUSTOMER)
            self.__safe_remotion(ride_info["driver_id"], customer_id, ride_info["id"])

    def __remove_driver(self, driver_id):
        print(f"Remove {driver_id}")
        driver = self.__drivers[driver_id]
        driver_info = driver.get_info()
        self.__drivers_by_state[driver_info["state"].value].remove(driver_id)
        self.__drivers_by_state[DriverState.INACTIVE.value].append(driver_id)
        driver_info = driver.set_state(DriverState.INACTIVE)
        self.__sim_drivers_ids.remove(driver_id)
        if driver_id in traci.vehicle.getIDList():
            traci.vehicle.remove(driver_id)
        else:
            print(f"Driver {driver_id} already removed...")

    def __remove_driver_by_state(self, driver_id):
        #print(f"{driver_id} disappeared from the simulation")
        driver = self.__drivers[driver_id]
        driver_info = driver.get_info()
        #print(f"{driver_id} current_coordinates: {driver_info['current_coordinates']}")
        #print(f"{driver_id} current edge: {traci.simulation.convertRoad(driver_info['current_coordinates'][0], driver_info['current_coordinates'][1])}")
        #print(f"{driver_id} state: {driver_info['state']}")

        if driver_info["state"] in [DriverState.IDLE, DriverState.MOVING]:
            print(16)
            self.__remove_driver(driver_id)
        elif driver_info["state"] in [DriverState.RESPONDING]:
            ride_info = self.__provider.find_ride_by_agent_id(driver_info, HumanType.DRIVER)
            if ride_info is None:
                print(ride_info)
                print(driver_info)
            ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
            ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
            print(17)
            self.__remove_driver(driver_id)
        elif driver_info["state"] in [DriverState.PICKUP, DriverState.ON_ROAD]:
            ride_info = self.__provider.find_ride_by_agent_id(driver_info, HumanType.DRIVER)
            self.__safe_remotion(driver_info["id"], ride_info["customer_id"], ride_info["id"])

    def __save_areas_info_agents(self, timestamp):
        area_ids = self.__map.get_area_ids()
        for area_id in area_ids:
            area_info = self.__map.get_area_info(area_id)
            drivers_in_area = self.__get_drivers_in_area(area_id)
            drivers_in_area_array = drivers_in_area.values()
            customers_in_area = self.__get_customers_in_area(area_id)
            customers_in_area_array = customers_in_area.values()
            idle_drivers_in_area = list(filter(lambda d: d["state"] == DriverState.IDLE, drivers_in_area_array))
            responding_drivers_in_area = list(filter(lambda d: d["state"] == DriverState.RESPONDING, drivers_in_area_array))
            pickup_drivers_in_area = list(filter(lambda d: d["state"] == DriverState.PICKUP, drivers_in_area_array))
            on_road_drivers_in_area = list(filter(lambda d: d["state"] == DriverState.ON_ROAD, drivers_in_area_array))
            moving_drivers_in_area = list(filter(lambda d: d["state"] == DriverState.MOVING, drivers_in_area_array))
            active_customers = list(filter(lambda d: d["state"] == CustomerState.ACTIVE, customers_in_area_array))
            pending_customers = list(filter(lambda d: d["state"] == CustomerState.PENDING, customers_in_area_array))
            pickup_customers = list(filter(lambda d: d["state"] == CustomerState.PICKUP, customers_in_area_array))
            on_road_customers = list(filter(lambda d: d["state"] == CustomerState.ON_ROAD, customers_in_area_array))
            energy_indexes = self.__energy_indexes.get_energy_indexes()
            num_not_accomplished = 0
            start_timestamp = int(timestamp) - 100 if timestamp >= 100 else 0
            for i in range(start_timestamp + 1, int(timestamp)):
                num_not_accomplished += energy_indexes["not_accomplished"][i]
            balance = self.__provider.compute_balance(len(pending_customers) + len(active_customers), len(idle_drivers_in_area) + len(responding_drivers_in_area), num_not_accomplished)

            statistics = {
                "area_id": area_id,
                "idle_drivers": len(idle_drivers_in_area),
                "responding_drivers": len(responding_drivers_in_area),
                "pickup_drivers": len(pickup_drivers_in_area),
                "on_road_drivers": len(on_road_drivers_in_area),
                "moving_drivers": len(moving_drivers_in_area),
                "active_customers": len(active_customers),
                "pending_customers": len(pending_customers),
                "pickup_customers": len(pickup_customers),
                "on_road_customers": len(on_road_customers),
                "balance": round(balance,2)
            }
            self.__printer.save_areas_info_agents(timestamp, statistics)
            #print(statistics)

    def __safe_remotion(self, driver_id, customer_id, ride_id):
        print(1)
        self.__remove_driver(driver_id)
        self.__remove_customer(customer_id)
        self.__provider.remove_ride_simulation_error(ride_id)

    def __send_request_to_driver(self, driver_id):
        driver = self.__drivers[driver_id]
        self.__drivers_by_state[DriverState.IDLE.value].remove(driver_id)
        self.__drivers_by_state[DriverState.RESPONDING.value].append(driver_id)
        return driver.receive_request()

    def __set_driver_route(self, driver_id, route_id, stop_pos=-1, flags=0, duration=3):
        driver = self.__drivers[driver_id]
        route = traci.route.getEdges(route_id)
        destination_edge_id = route[-1]
        if stop_pos == -1:
            destination_edge = self.__sumo_net.getEdge(destination_edge_id)
            edge_length = destination_edge.getLength()
            stop_pos = random.random() * edge_length
        try:
            traci.vehicle.setRouteID(driver_id, route_id)
            traci.vehicle.setStop(driver_id, destination_edge_id, stop_pos, duration=duration, flags=flags)
        except:
            raise Exception(f"Simulation.__set_driver_route - Impossible to set driver route for {driver_id}")
        driver.set_route_destination_position(stop_pos)

    def __start_sumo_route(self, timestamp, driver_id, customer_id=None, ride_id=None, area_id=None):
        driver = self.__drivers[driver_id]
        driver_info = driver.get_info()

        if driver_info["state"] == DriverState.PICKUP:
            assert customer_id is not None, "Simulator.__start_sumo_route - customer id is None."
            destination_edge_id = traci.person.getEdges(customer_id)[0]
            edge_length = self.__sumo_net.getEdge(destination_edge_id).getLength()
            try:
                destination_position = traci.person.getLanePosition(customer_id) if traci.person.getLanePosition(customer_id) > 0 else min(0.2, edge_length)
                print(f"Pickup route for driver {driver_info['id']} and customer {customer_id}.")
                self.__set_driver_route(driver_id, driver_info["route"]["id"], destination_position, flags=2, duration=2)
            except Exception as e:
                print(e)
                print("Simulator.__start_sumo_route - ride removed because of error in generating route.")
                assert ride_id is not None, "Simulator.__start_sumo_route - ride id is None."
                #self.__safe_remotion(driver_id, customer_id, ride_id)
                driver_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(
                    driver_info["current_coordinates"]), "driver")
                if not driver_area_id == "unknown":
                    self.__generate_driver(timestamp, driver_area_id, last_ride_timestamp=driver_info["last_ride_timestamp"], rides_completed=driver_info["rides_completed"])
                print(2)
                self.__remove_driver(driver_id)
                raise Exception("Simulator.__start_sumo_route - ride removed because of error in generating route.")
        elif driver_info["state"] == DriverState.ON_ROAD:
            destination_route = driver_info["route"]["route"]
            destination_route_id = driver_info["route"]["id"]
            #destination_edge_id = destination_route[-1]
            #destination_edge = self.__sumo_net.getEdge(destination_edge_id)
            #random_position = (round(random.uniform(0.05, 0.95), 2)) * destination_edge.getLength()
            traci.person.appendDrivingStage(customer_id, destination_route[-1], driver_info["id"])
            traci.person.appendWaitingStage(customer_id, 5)
            traci.person.removeStage(customer_id, 0)
            destination_position = traci.person.getStage(customer_id).arrivalPos
            try:
                self.__set_driver_route(driver_id, destination_route_id, stop_pos=destination_position)
            except:
                self.__safe_remotion()
        elif driver_info["state"] == DriverState.IDLE:
            assert customer_id is not None, "Simulator.__start_sumo_route - customer id is None."
            driver = self.__drivers[driver_id]
            driver_info = driver.get_info()
            driver_area_id = self.check_area_id(driver_info,self.__map.get_area_from_coordinates(driver_info["current_coordinates"]), 'driver')
            assert area_id is not None, f"Simulator.start_sumo route - destination area is None."
            #assert (not driver_area == "unknown") and type(driver_area) == str, f"Simulator.__start_sumo_route - Unexpected unknown id area ({driver_info['current_coordinates']}) for customer {driver_info['id_customer']}."
            if driver_area_id == "unknown":
                print(3)
                self.__remove_driver_by_state(driver_id)
                return
            assert not driver_area_id == area_id, "Simulator.__start_sumo_route - driver area is equal to area where the driver have to move"
            area_info = self.__map.get_area_info(area_id)
            hexagon_random_id = utils.select_from_list(area_info["hexagons"])
            ways = self.__map.get_hexagon_info(hexagon_random_id)["ways"]
            way_random_id = utils.select_from_list(ways)
            destination_position = self.__map.get_random_position_from_way(way_random_id)
            try:
                route = Map.generate_route_from_agent_to_destination_point(timestamp, self.__sumo_net, driver_info, HumanType.DRIVER, destination_position)
                self.__set_driver_route(driver_info["id"], route.get_route_id())
                driver.set_route(route)
                driver.set_state(DriverState.MOVING)
            except:
                print("Simulator.__start_sumo_route - Impossible to move driver to the destination area.")
                driver_info = self.__drivers[driver_id].get_info()
                self.__generate_driver(timestamp, driver_area_id, last_ride_timestamp=driver_info["last_ride_timestamp"], rides_completed=driver_info["rides_completed"])
                print(4)
                self.__remove_driver(driver_id)
                raise Exception("Simulator.__start_sumo_route - Impossible to move driver to the destination area.")
        else:
            raise Exception(f"Simulator.__start_sumo_route - unexpected driver state {driver_info['state']}")

    def __trigger_event(self, e):
        self.__map.update_generation_policy(e["area_id"], e["generation_policy"])

    def __update_coordinates_and_distance(self, timestamp):
        drivers_snapshot = [*self.__drivers.values()]
        for driver in drivers_snapshot:
            driver_info = driver.get_info()
            if (not driver_info["state"] == DriverState.INACTIVE) and driver_info["id"] in traci.vehicle.getIDList():
                destination_point = driver_info["route"]["destination_point"]
                current_coordinates = Map.get_sumo_current_coordinates(driver_info, HumanType.DRIVER)
                driver.set_coordinates(current_coordinates)
                driver_info = driver.set_current_distance(Map.compute_distance(current_coordinates, destination_point))

        customers_snapshot = [*self.__customers.values()]
        for customer in customers_snapshot:
            customer_info = customer.get_info()
            if (not customer_info["state"] == CustomerState.INACTIVE) and customer_info["id"] in traci.person.getIDList():
                current_coordinates = Map.get_sumo_current_coordinates(customer_info, HumanType.CUSTOMER)
                customer.set_coordinates(current_coordinates)

    def __update_drivers(self, timestamp):
        active_drivers = [*self.__drivers_by_state[DriverState.MOVING], *self.__drivers_by_state[DriverState.IDLE], *self.__drivers_by_state[DriverState.RESPONDING]]
        for driver_id in active_drivers:
            driver = self.__drivers[driver_id]
            driver_info = driver.get_info()
            if driver_info["state"] == DriverState.MOVING:
                assert not driver_info["route"] == None, "Simulator.updateDrivers - unexpected moving driver without route"
                assert not driver_info["current_distance"] == None, "Simulator.updateDrivers - unexpected driver distance undefined"
                if Map.is_arrived_by_sumo_edge(self.__sumo_net, driver_info):
                    print(f"Route completed for driver {driver_info['id']} - [1]")
                    try:
                        print(f"Simulator.__update_drivers | Driver {driver_info['id']} - generate random route [1]")
                        random_route = self.__map.generate_random_route_in_area_from_agent(timestamp, self.__sumo_net, driver_info, HumanType.DRIVER)
                        self.__set_driver_route(driver_info["id"], random_route.get_route_id())
                        self.__drivers_by_state[DriverState.MOVING.value].remove(driver_info["id"])
                        self.__drivers_by_state[DriverState.IDLE.value].append(driver_info["id"])
                        driver_info = driver.update_end_moving(random_route)
                    except:
                        print(f"Simulator.__update_drivers - Impossible to find route. Driver {driver_info['id']} removed.")
                        driver_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(driver_info["current_coordinates"]), "driver")
                        if not driver_area_id == "unknown":
                            self.__generate_driver(timestamp, driver_area_id, last_ride_timestamp=driver_info["last_ride_timestamp"], rides_completed=driver_info["rides_completed"])
                        print(5)
                        self.__remove_driver(driver_id)
            elif driver_info["state"] in [DriverState.IDLE, DriverState.RESPONDING]:
                area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(driver_info["current_coordinates"]), 'driver')
                #assert (not area_id == 'unknown') and type(area_id) == str, f"Simulator.__update_drivers - Unexpected unknown id area ({driver_info['current_coordinates']}) for driver {driver_info['id']}"
                if area_id == "unknown":
                    if driver_info["state"] == DriverState.IDLE:
                        print(6)
                        self.__remove_driver(driver_id)
                        continue
                    elif driver_info["state"] == DriverState.RESPONDING:
                        ride_info = self.__provider.find_ride_by_agent_id(driver_info, HumanType.DRIVER)
                        ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
                        ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
                        print(7)
                        self.__remove_driver(driver_id)
                        continue
                area_info = self.__map.get_area_info(area_id)
                surge_multiplier = area_info["surge_multipliers"][0]
                last_ride_timestamp = driver.get_info()["last_ride_timestamp"]
                idle_time_over = (timestamp - last_ride_timestamp) > self.__simulator_setup["timer_remove_idle_driver"]
                if idle_time_over and driver_info["state"] == DriverState.IDLE:
                    print(8)
                    print(f"Driver {driver_id} stop to work [1]")
                    self.__remove_driver(driver_info["id"])
                    continue
                elif surge_multiplier <= 1 and driver_info["state"] == DriverState.IDLE:
                    stop_policy = self.__driver_setup["stop_work_policy"]
                    stop_probability = (timestamp - last_ride_timestamp) * self.__get_human_policy(stop_policy, driver_info["personality"])
                    #print(f"{stop_probability} - {last_ride_timestamp} - {self.__get_human_policy(stop_policy, driver_info['personality'])}")
                    if utils.random_choice(stop_probability):
                        print(9)
                        print(f"Driver {driver_id} stop to work [2]")
                        self.__remove_driver(driver_info["id"])
                        continue
                if Map.is_arrived_by_sumo_edge(self.__sumo_net, driver_info):
                    try:
                        print(f"Route completed for driver {driver_info['id']} [2]")
                        print(f"Simulator.__update_drivers | Driver {driver_info['id']} - generate random route [2]")
                        random_route = self.__map.generate_random_route_in_area_from_agent(timestamp, self.__sumo_net, driver_info, HumanType.DRIVER)
                        self.__set_driver_route(driver_info["id"], random_route.get_route_id())
                    except Exception as e:
                        print(e)
                        driver_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(
                            driver_info["current_coordinates"]), "driver")
                        if not driver_area_id == "unknown":
                            self.__generate_driver(timestamp, driver_area_id, last_ride_timestamp=driver_info["last_ride_timestamp"], rides_completed=driver_info["rides_completed"])
                        if driver_info["state"] in [DriverState.RESPONDING]:
                            ride_info = self.__provider.find_ride_by_agent_id(driver_info, HumanType.DRIVER)
                            if ride_info is None:
                                print(ride_info)
                                print(driver_info)
                            ride_info = self.__provider.ride_request_rejected(ride_info["id"], driver_id)
                            ride_info = self.__provider.set_ride_request_state(ride_info["id"], RideRequestState.REJECTED)
                        print(10)
                        self.__remove_driver(driver_id)



    def __update_driver_movements(self, timestamp):
        active_drivers = list(map(lambda d_id: self.__drivers[d_id], self.__drivers_by_state[DriverState.IDLE]))
        if len(active_drivers) > 0:
            for area_id in self.__map.get_area_ids():
                area_info = self.__map.get_area_info(area_id)
                move_probability = 0
                for other_area_id in self.__map.get_area_ids():
                    if not area_id == other_area_id:
                        other_area_info = self.__map.get_area_info(area_id)
                        for min_diff, max_diff, probability in self.__driver_setup["move_policy"]["move_diff_probabilities"]:
                            surge_multiplier_area = area_info["surge_multipliers"][0]
                            surge_multiplier_other_area = other_area_info["surge_multipliers"][0]
                            diff_surge_multiplier = surge_multiplier_area - surge_multiplier_other_area
                            if min_diff < diff_surge_multiplier < max_diff:
                                move_probability = probability
                                break
                        for driver_id in self.__get_drivers_in_area(other_area_id):
                            driver_info = self.__drivers[driver_id].get_info()
                            if driver_info["state"] == DriverState.IDLE:
                                if utils.random_choice(move_probability):
                                    self.__move_driver_to_area(timestamp, driver_id, area_id)

    def __update_rides_state(self, timestamp):
        pickup_rides = self.__provider.get_rides_info_by_state(RideState.PICKUP.value)
        on_road_rides = self.__provider.get_rides_info_by_state(RideState.ON_ROAD.value)

        for ride_info in pickup_rides:
            assert not ride_info["driver_id"] == None, "Simulator.__update_rides_state - unexpected id driver undefined [1]"
            driver = self.__drivers[ride_info["driver_id"]]
            driver_info = driver.get_info()
            assert not driver_info["current_distance"] == None, "Simulator.__update_rides_state - unexpected driver distance undefined. [1]"
            if Map.is_arrived_by_sumo_edge(self.__sumo_net, driver_info):
                print(f"Route completed for driver {driver_info['id']} [3]")
                customer = self.__customers[ride_info["customer_id"]]
                customer_info = customer.update_on_road()
                assert not ride_info["routes"]["destination_route"] == None, "Simulator.__update_rides_state - destination route not found on pickup."
                destination_route = self.__provider.get_ride_destination_route(ride_info["id"])
                destination_route_edges = destination_route.get_route()
                try:
                    driver_current_edge = traci.vehicle.getRoute(driver_info["id"])[traci.vehicle.getRouteIndex(driver_info["id"])]
                except:
                    print(f"Simulator.__update_rides_state - {driver_info['id']} not found.")
                    self.__safe_remotion(driver_info["id"], customer_info["id"], ride_info["id"])
                if not driver_current_edge == destination_route_edges[0]:
                    try:
                        ride_info, destination_route = self.__refine_ride_route(timestamp, driver_info["id"], ride_info["id"], destination_route, "destination_route")
                    except Exception as e:
                        print(f"Simulator.__update_rides_state - Impossible to generate a refined route from {driver_current_edge} to {destination_route_edges[-1]}.")
                        self.__safe_remotion(driver_info["id"], customer_info["id"], ride_info["id"])
                driver_info = driver.update_on_road(destination_route)
                self.__drivers_by_state[DriverState.PICKUP.value].remove(driver_info["id"])
                self.__drivers_by_state[DriverState.ON_ROAD.value].append(driver_info["id"])
                self.__customers_by_state[DriverState.PICKUP.value].remove(customer_info["id"])
                self.__customers_by_state[DriverState.ON_ROAD.value].append(customer_info["id"])
                assert (not ride_info["stats"]["timestamp_pickup"] == None), "Simulator.__update_rides_state - statistic [timestampPickup] not found or wrong type"
                meeting_duration = timestamp - ride_info["stats"]["timestamp_pickup"]
                assert not ride_info["routes"]["meeting_route"] == None, "Simulator.__update_rides_state - meeting route not found on pickup."
                # this should be change according to an algorithm that compute the actual distance covered
                meeting_route = self.__provider.get_ride_meeting_route(ride_info["id"])
                meeting_distance = meeting_route.get_original_distance()
                stats = {
                    "timestamp_on_road": timestamp,
                    "meeting_duration": meeting_duration,
                    "meeting_length": meeting_distance
                }
                ride_info = self.__provider.update_ride_on_road(ride_info["id"], stats)
                driver_info = driver.set_current_distance((math.inf, math.inf))
                try:
                    self.__start_sumo_route(timestamp, driver_info["id"], customer_info["id"], ride_info["id"])
                except:
                    print("Simulator.__update_rides_state - Impossible to start sumo route")
            driver_info = driver.set_current_distance(Map.compute_distance(driver_info["current_coordinates"], ride_info["meeting_point"]))

        for ride_info in on_road_rides:
            assert not ride_info["driver_id"] == None, "Simulator.__update_rides_state - unexpected id driver distance undefined [2]"
            driver = self.__drivers[ride_info["driver_id"]]
            driver_info = driver.get_info()
            assert not driver_info["current_distance"] == None, "Simulator.__update_rides_state - unexpected driver distance undefined. [2]"
            try:
                if Map.is_arrived_by_sumo_edge(self.__sumo_net, driver_info):
                    people_in_vehicle = traci.vehicle.getPersonNumber(driver_info['id'])
                    if people_in_vehicle == 0:
                        print(f"Route completed for driver {driver_info['id']} [4]")
                        customer = self.__customers[ride_info["customer_id"]]
                        customer_info = customer.update_end()
                        self.__customers_by_state[CustomerState.ON_ROAD.value].remove(customer_info["id"])
                        self.__customers_by_state[CustomerState.INACTIVE.value].append(customer_info["id"])
                        self.__sim_customers_ids.remove(customer_info["id"])
                        assert (not ride_info["stats"]["timestamp_on_road"] == None) and type(ride_info["stats"]["timestamp_on_road"]), "Simulator.__update_rides_state - statistic [timestampOnRoad] not found or wrong type"
                        destination_duration = timestamp - ride_info["stats"]["timestamp_on_road"]
                        assert not ride_info["routes"]["destination_route"] == None, "Simulator.__update_rides_state - destination route not found on road."
                        # this should be change according to an algorithm that compute the actual distance covered
                        destination_distance = ride_info["routes"]["destination_route"]["original_distance"]
                        assert not ride_info["stats"]["surge_multiplier"] == None, "Simulator.__update_rides_state - surge multiplier undefined."
                        surge_multiplier = ride_info["stats"]["surge_multiplier"]
                        price = self.__provider.compute_price(destination_duration, destination_distance, surge_multiplier)
                        stats = {
                            "timestamp_end": timestamp,
                            "ride_length": destination_distance,
                            "ride_duration": destination_duration,
                            "price": price
                        }
                        ride_info = self.__provider.update_ride_end(ride_info["id"], stats)
                        self.__printer.save_specific_indicators(timestamp, ride_info)
                        self.__energy_indexes.compute_ovehead(timestamp, ride_info["stats"]["timestamp_request"], destination_duration)
                        self.__energy_indexes.compute_price_fluctuation(timestamp, price, ride_info["stats"]["expected_price"])
                        try:
                            print(f"Simulator.__update_rides_state | Driver {driver_info['id']} - generate random route")
                            random_route = self.__map.generate_random_route_in_area_from_agent(timestamp, self.__sumo_net, driver_info, HumanType.DRIVER)
                            self.__set_driver_route(driver_info["id"], random_route.get_route_id())
                            self.__drivers_by_state[DriverState.ON_ROAD.value].remove(driver_info["id"])
                            self.__drivers_by_state[DriverState.IDLE.value].append(driver_info["id"])
                            driver_info = driver.update_end(timestamp, random_route)
                        except Exception as e:
                            #print(e)
                            print(f"Simulator.__update_ride_stats - Impossible to find route. Driver {driver_info['id']} removed.")
                            driver_area_id = self.check_area_id(driver_info, self.__map.get_area_from_coordinates(driver_info["current_coordinates"]), "driver")
                            if not driver_area_id == "unknown":
                                self.__generate_driver(timestamp, driver_area_id, last_ride_timestamp=driver_info["last_ride_timestamp"], rides_completed=driver_info["rides_completed"])
                            print(11)
                            self.__remove_driver(driver_info["id"])
            except:
                print(f"Simulator.__update_rides_state | Driver {driver_info['id']} not found in calling Map.is_arrived_by_sumo_edge method.")
                self.__safe_remotion(driver_info["id"], ride_info["customer_id"], ride_info["id"])
            driver_info = driver.set_current_distance(Map.compute_distance(driver_info["current_coordinates"], ride_info["destination_point"]))

    def __update_surge_multiplier(self, timestamp):
        area_ids = self.__map.get_area_ids()
        #pending_rides = self.__provider.get_pending_rides()
        #pending_request_areas = list(map(lambda r: self.__map_pending_request_area(r), pending_rides))
        for area_id in area_ids:
            area_info = self.__map.get_area_info(area_id)
            drivers_in_area = self.__get_drivers_in_area(area_id)
            drivers_in_area_array = drivers_in_area.values()
            idle_drivers_in_area = list(filter(lambda d: d["state"] in [DriverState.IDLE, DriverState.RESPONDING], drivers_in_area_array))
            responding_drivers_in_area = list(filter(lambda d: d["state"] == DriverState.RESPONDING, drivers_in_area_array))
            surge_multiplier = area_info["surge_multipliers"][0]
            customers_in_area = self.__get_customers_in_area(area_id)
            customers_in_area_array = customers_in_area.values()
            #idle_customers = list(filter(lambda r: r["area_request_id"] == area_id, pending_request_areas))
            pending_customers = list(filter(lambda d: d["state"] in [CustomerState.ACTIVE, CustomerState.PENDING], customers_in_area_array))
            energy_indexes = self.__energy_indexes.get_energy_indexes()
            num_not_accomplished = 0
            start_timestamp = int(timestamp) - 100 if timestamp >= 100 else 0
            for i in range(int(start_timestamp) + 1, int(timestamp)):
                num_not_accomplished += energy_indexes["not_accomplished"][i]
            balance = self.__provider.compute_balance(len(pending_customers), len(idle_drivers_in_area) + len(responding_drivers_in_area), num_not_accomplished)
            self.__map.update_area_balance(area_id, balance)
            surge_multiplier_increment = self.__provider.compute_surge_multiplier_increment(balance)
            new_surge_multiplier = max(0.7, min(surge_multiplier + surge_multiplier_increment, 3.5))
            self.__map.update_area_surge_multiplier(area_id, new_surge_multiplier)

    def run(self):
        step = 0
        stop = False
        while not stop:
            traci.simulationStep()
            timestamp = traci.simulation.getTime()
            print(f"timestamp: {timestamp}")
            self.__check_drivers_list(timestamp)
            self.__check_customers_list(timestamp)
            self.__update_coordinates_and_distance(timestamp)
            try:
                if utils.random_choice(0.8):
                    self.__generate_customer_requests(timestamp)
                self.__process_rides(timestamp)
                self.__manage_pending_request(timestamp)
                if timestamp % 10.0 == 0:
                    self.__update_surge_multiplier(timestamp)
                self.__update_drivers(timestamp)
                self.__update_rides_state(timestamp)
                timestamp_generation_events = self.__timeline_generation[str(int(timestamp))]
                for area_id in timestamp_generation_events["customers"]:
                    if area_id in self.__map.get_area_ids():
                        self.__generate_customer(timestamp, area_id)
                for area_id in timestamp_generation_events["drivers"]:
                    if area_id in self.__map.get_area_ids():
                        self.__generate_driver(timestamp, area_id)
                if (timestamp % self.__simulator_setup["checkpoints"]["time_move_driver"]) == 0.0:
                    self.__update_driver_movements(timestamp)
                scenario_events = self.__scenario.check_events(timestamp)
                for event_type, params in scenario_events:
                    self.__perform_scenario_event(timestamp, event_type, params)

                if timestamp % 100.0 == 0:
                    self.__printer.export_global_indicators()
                    self.__printer.export_global_indicators_v2()
                    self.__printer.export_specific_indicators()
                    self.__printer.export_rides_assignations()
                    self.__printer.export_surge_multipliers()
                    self.__printer.export_areas_info_agents_statistics()
                    self.print_drivers_by_state()
                    self.print_customers_by_state()
                if timestamp >= 100 and timestamp % 100.0 == 0:
                    self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 100)
                if timestamp >= 200 and timestamp % 100.0 == 0:
                    self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 200)
                if timestamp >= 500 and timestamp % 100.0 == 0:
                    self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 500)
                if timestamp % 5000.0 == 0:
                    stop = True
                    print("STOP")
                    self.__printer.export_global_indicators()
                    self.__printer.export_global_indicators_v2()
                    self.__printer.export_specific_indicators()
                    self.__printer.export_rides_assignations()
                    self.__printer.export_surge_multipliers()
                if timestamp == 1.0:
                    self.__printer.save_specific_indicators(timestamp)
                    self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 100)
                    self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 200)
                    self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 500)
                #print(self.__drivers_by_state)
                #print(self.__customers_by_state)
                #print(self.__sim_drivers_ids)
                #print(traci.vehicle.getIDList())
                #print(self.__sim_customers_ids)
                #print(traci.person.getIDList())
                self.__printer.save_global_indicators(timestamp, self.__provider.get_rides_info_by_state("all"))
                self.__printer.save_global_indicators_v2(timestamp, self.__provider.get_rides_info_by_state("all"))
                self.__printer.save_surge_multipliers(timestamp, self.__map.get_areas_info())
                self.__save_areas_info_agents(timestamp)
                print(f"Customers: {len(traci.person.getIDList())}")
                print(f"Drivers: {len(traci.vehicle.getIDList())}")
            except Exception as e:
                self.print_drivers()
                print(self.__drivers_by_state)
                print(self.__customers_by_state)
                print(e)
                self.__printer.export_global_indicators()
                self.__printer.export_global_indicators_v2()
                self.__printer.export_specific_indicators()
                self.__printer.export_rides_assignations()
                self.__printer.export_surge_multipliers()
                self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 100)
                self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 200)
                self.__printer.export_energy_indexes(timestamp, self.__energy_indexes.get_energy_indexes(), 500)
                raise Exception("A Fatal error occurred in Simulator.run")
        traci.close(False)
        sys.stdout.flush()

    def print_customers(self):
        customers_info = []
        for customer in self.__customers.values():
            customers_info.append(customer.get_info())
        print(customers_info)

    def print_drivers(self):
        for driver in self.__drivers.values():
            driver_info = driver.get_info()
            print(f"Driver info: {driver_info}")
            if driver_info["id"] in traci.vehicle.getIDList():
                print(f"Driver route index: {traci.vehicle.getRouteIndex(driver_info['id'])}")
            #if len(traci.vehicle.getRoute(driver_info['id'])) > 0:
                #print(f"Driver current edge: {traci.vehicle.getRoute(driver_info['id'])[traci.vehicle.getRouteIndex(driver_info['id'])]}")

    def print_person(self):
        for person_id in traci.person.getIDList():
            print(f"Person current edge: {traci.person.getEdges(person_id)}")

    def print_drivers_by_state(self):
        print(self.__drivers_by_state)

    def print_customers_by_state(self):
        print(self.__customers_by_state)

    def get_drivers(self):
        return self.__drivers