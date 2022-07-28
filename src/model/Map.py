import copy
import math
import random
import re

import h3
from src.utils import utils
from src.state.HumanType import HumanType
from src.model.Route import Route
from src.state.DriverState import DriverState
import sumolib
import traci


class Map:
    def __init__(self, map, resolution):
        self.__areas = map["areas"]
        self.__hexagons = map["hexagons"]
        self.__pois = map["pois"]
        self.__ways = map["ways"]
        self.__resolution = resolution

    @staticmethod
    def add_sumo_route_to_simulation(sumo_route_id, sumo_route):
        if not (sumo_route_id in traci.route.getIDList()):
            traci.route.add(sumo_route_id, sumo_route.edges)
        else:
            print("Route id already exist")

    @staticmethod
    def compute_distance(current_coordinates, reference_coordinates):
        if type(current_coordinates[0]) == str or type(current_coordinates[1]) == str or type(reference_coordinates[0]) == str or type(reference_coordinates[1]) == str:
            print(current_coordinates)
            print(reference_coordinates)
        return (
            abs(current_coordinates[0] - reference_coordinates[0]),
            abs(current_coordinates[1] - reference_coordinates[1])
        )

    def find_near_hexagon(self, sumo_net, hexagon_id):
        hexagon_ring = self.get_near_hexagons(hexagon_id, 20)
        for ring in hexagon_ring:
            for near_hexagon in ring:
                area_id = self.get_area_from_hexagon(near_hexagon)
                if not area_id == "unknown":
                    try:
                        return self.generate_coordinates_from_hexagon(sumo_net, area_id, near_hexagon)
                    except:
                        print(f"Map.find_near_hexagon - New coordinates in near hexagon {near_hexagon} not found.")
                        continue
        print("Map.find_near_hexagon - New coordinates not found")
        return None

    def generate_coordinates_from_hexagon(self, sumo_net, area_id, hexagon_id="random", must_be_edge=True):
        area = self.__areas[area_id]
        is_random = True
        if not hexagon_id == "random":
            assert hexagon_id in area["hexagons"], "Map.generate_coordinates_from_hexagon - Id hexagon dose not belong to area"
        hexagons = copy.deepcopy(area["hexagons"])
        while len(hexagons) > 0:
            if hexagon_id == "random":
                hexagon_id = utils.select_from_list(hexagons)
            else:
                is_random = False
            hexagons.remove(hexagon_id)
            hexagon_ways = [*self.__hexagons[hexagon_id]["ways"]]
            while len(hexagon_ways) > 0:
                way_id = utils.select_from_list(hexagon_ways)
                hexagon_ways.remove(way_id)
                position = self.get_random_position_from_way(sumo_net, way_id, must_be_edge=must_be_edge)
                if position is not None:
                    return position
            if not is_random:
                raise Exception("Map.generate_coordinates_from_hexagon - no way found")
        raise Exception("Map.generate_coordinates_from_hexagon - no way found")

    def generate_destination_point(self, sumo_net, start_point, distance):
        start_hexagon = h3.geo_to_h3(start_point[1], start_point[0], self.__resolution)
        ring_distance = distance - math.floor(random.random() * 2)
        if ring_distance < 1:
            print(ring_distance)
        candidate_hexagons = h3.k_ring_distances(start_hexagon, ring_distance)
        for i in range(ring_distance, 0, -1):
            ring_candidates = candidate_hexagons[i].intersection(self.__hexagons.keys())
            found = False
            while (len(ring_candidates) > 0 and not found):
                id_destination_hexagon = list(ring_candidates).pop(math.floor(random.random() * len(ring_candidates)))
                assert id_destination_hexagon is not None, "Map.generate_destination_point - Id destination hexagon is undefined"
                if self.__hexagons[id_destination_hexagon] is not None:
                    found = True
                    candidate_ways = self.__hexagons[id_destination_hexagon]["ways"]
                    id_destination_way = utils.select_from_list(candidate_ways)
                    position_destination = self.get_random_position_from_way(sumo_net, id_destination_way)
                    return position_destination
        assert False, "Map.generate_destination_point - destination not found"
        return start_point

    def generate_destination_point_from_hexagon(self, sumo_net, destination_hexagon):
        assert destination_hexagon in self.__hexagons, "Map.generate_destination_point_from_hexagon - destination hexagon not found"
        assert len(self.__hexagons[destination_hexagon]["ways"]) > 0 , "Map.generate_destination_point_from_hexagon - destination hexagon has not ways"
        candidate_ways = self.__hexagons[destination_hexagon]["ways"]
        id_destination_way = utils.select_from_list(candidate_ways)
        position_destination = self.get_random_position_from_way(sumo_net, id_destination_way)
        return position_destination

    def generate_random_route_in_area(self, timestamp, sumo_net, start_point):
        area_id = self.get_area_from_coordinates(start_point)
        start_hexagon = self.get_hexagon_id_from_coordinates(start_point)
        destination_hexagon = self.get_random_hexagon_from_area(area_id, exclude_hexagons=[start_hexagon])
        destination_point = self.generate_destination_point_from_hexagon(sumo_net, destination_hexagon)
        try:
            random_route = self.generate_route_from_coordinates(timestamp, sumo_net, [start_point, destination_point])
            return random_route
        except:
            error_msg = f"Map.generate_random_route_in_area - Route impossible: no connection between the source {start_point} and the desitnation {destination_point}."
            print(error_msg)
            raise Exception(error_msg)

    def generate_random_route_in_area_from_agent(self, timestamp, sumo_net, agent_info, agent_type):
        area_id = self.get_area_from_coordinates(agent_info["current_coordinates"])
        start_hexagon = self.get_hexagon_id_from_coordinates(agent_info["current_coordinates"])
        destination_hexagon = self.get_random_hexagon_from_area(area_id, exclude_hexagons=[start_hexagon])
        destination_point = self.generate_destination_point_from_hexagon(sumo_net, destination_hexagon)
        try:
            return self.generate_route_from_agent_to_destination_point(timestamp, sumo_net, agent_info, agent_type, destination_point)
        except:
            raise Exception(f"Map.generate_random_route_in_area_from_agent - Impossible to generate route from agent {agent_info} to coordinates {destination_point}")

    @staticmethod
    def generate_route_from_coordinates(timestamp, sumo_net, waypoints):
        from_edge_id = Map.get_sumo_edge_id_from_coordinates(sumo_net, waypoints[0])
        to_edge_id = Map.get_sumo_edge_id_from_coordinates(sumo_net, waypoints[1])
        sumo_route = traci.simulation.findRoute(from_edge_id, to_edge_id)
        sumo_route_distance = sumo_route.length
        sumo_route_duration = sumo_route.travelTime
        sumo_route_id = f"route_from_{from_edge_id}_to_{to_edge_id}"
        if len(sumo_route.edges) > 0:
            Map.add_sumo_route_to_simulation(sumo_route_id, sumo_route)
            return Route(timestamp, waypoints[0], waypoints[1], "sumo", sumo_route_id, sumo_route.edges, sumo_route_distance, sumo_route_duration)
        else:
            error_msg =f"Map.generate_route_from_coordinates - Route impossible: no connection between the source {waypoints[0]} and the desitnation {waypoints[1]}."
            print(error_msg)
            raise Exception(error_msg)

    @staticmethod
    def generate_route_from_agents(timestamp, from_agent_info, from_agent_type, to_agent_info, to_agent_type):
        from_edge_id = Map.get_edge_id_from_agent(from_agent_info, from_agent_type)
        to_edge_id = Map.get_edge_id_from_agent(to_agent_info, to_agent_type)
        try:
            sumo_route_id, sumo_route = Map.generate_sumo_route_from_edge_ids(from_edge_id, to_edge_id)
            sumo_route_distance = sumo_route.length
            sumo_route_duration = sumo_route.travelTime
            Map.add_sumo_route_to_simulation(sumo_route_id, sumo_route)
            return Route(timestamp, from_agent_info["current_coordinates"], to_agent_info["current_coordinates"], 'sumo', sumo_route_id, sumo_route.edges, sumo_route_distance, sumo_route_duration)
        except:
            raise Exception(f"Map.generate_route_from_agents - Impossible to generate route from agent {from_agent_info['id']} to agent {to_agent_info['id']}")

    @staticmethod
    def generate_route_from_agent_to_destination_point(timestamp, sumo_net, from_agent_info, from_agent_type, to_coordinates):
        from_edge_id = Map.get_edge_id_from_agent(from_agent_info, from_agent_type)
        to_edge_id = Map.get_sumo_edge_id_from_coordinates(sumo_net, to_coordinates)
        try:
            sumo_route_id, sumo_route = Map.generate_sumo_route_from_edge_ids(from_edge_id, to_edge_id)
            sumo_route_distance = sumo_route.length
            sumo_route_duration = sumo_route.travelTime
            Map.add_sumo_route_to_simulation(sumo_route_id, sumo_route)
            return Route(timestamp, from_agent_info["current_coordinates"], to_coordinates, 'sumo', sumo_route_id, sumo_route.edges, sumo_route_distance, sumo_route_duration)
        except:
            raise Exception(f"Map.generate_route_from_agents - Impossible to generate route from agent {from_agent_info['id']} to coordinates {to_coordinates}")

    @staticmethod
    def generate_sumo_route_from_edge_ids(from_edge_id, to_edge_id):
        sumo_route = traci.simulation.findRoute(from_edge_id, to_edge_id)
        sumo_route_id = f"route_from_{from_edge_id}_to_{to_edge_id}"
        if len(sumo_route.edges) > 0:
            Map.add_sumo_route_to_simulation(sumo_route_id, sumo_route)
            return (sumo_route_id, sumo_route)
        else:
            error_msg = f"Map.generate_route_from_coordinates - Route impossible: no connection between the source {from_edge_id} and the desitnation {to_edge_id}."
            print(error_msg)
            raise Exception(error_msg)

    @staticmethod
    def get_air_distance(source_coordinates, destination_coordinates):
        return h3.point_dist((source_coordinates[1],source_coordinates[0]),(destination_coordinates[1], destination_coordinates[0]), unit='m')

    def get_area_from_coordinates(self, coordinates):
        hexagon_id = h3.geo_to_h3(coordinates[1], coordinates[0], self.__resolution)
        if not hexagon_id in self.__hexagons:
            return "unknown"
        area_id = self.__hexagons[hexagon_id]["area_id"]
        return area_id

    def get_area_from_hexagon(self, hexagon_id="random"):
        if not hexagon_id in self.__hexagons:
            return "unknown"
        area_id = self.__hexagons[hexagon_id]["area_id"]
        return area_id

    def get_area_ids(self):
        return self.__areas.keys()

    def get_area_info(self, area_id):
        return {
            **self.__areas[area_id]
        }

    def get_areas_info(self):
        areas_info = {}
        for area_id in self.__areas.keys():
            areas_info[area_id] = self.get_area_info(area_id)
        return areas_info

    @staticmethod
    def get_coordinates_from_hexagon_id(hexagon_id):
        h3_coordinates = h3.h3_to_geo(hexagon_id)
        return (h3_coordinates[1], h3_coordinates[0])

    @staticmethod
    def get_edge_id_from_agent(agent_info, agent_type):
        if agent_type == HumanType.DRIVER:
            driver_id = agent_info["id"]
            route_idx = traci.vehicle.getRouteIndex(driver_id)
            current_edge = traci.vehicle.getRoute(driver_id)[route_idx]
            return current_edge
        elif agent_type == HumanType.CUSTOMER:
            customer_id = agent_info["id"]
            current_edge = traci.person.getEdges(customer_id)[0]
            return current_edge
        else:
            raise Exception(f"Map.generate_sumo_route_from_agent_ids - Unknown from_agent_type {agent_type}")

    def get_hexagon_id_from_coordinates(self, coordinates):
        return h3.geo_to_h3(coordinates[1], coordinates[0], self.__resolution)

    def get_hexagon_info(self, hexagon_id):
        return {
            **self.__hexagons[hexagon_id]
        }

    @staticmethod
    def get_near_hexagons(hexagon_id, k_nearest):
        return h3.k_ring_distances(hexagon_id, k_nearest)

    def get_point_info(self, poi_id):
        return {
            **self.pois[poi_id]
        }

    def get_random_hexagon_from_area(self, area_id, exclude_hexagons=[]):
        area_hexagons = [*self.__areas[area_id]["hexagons"]]
        if len(exclude_hexagons) > 0:
            area_hexagons = list(filter(lambda h: not h in exclude_hexagons, area_hexagons))
        while len(area_hexagons) > 0:
            random_hexagon = utils.select_from_list(area_hexagons)
            hexagon_ways = self.__hexagons[random_hexagon]["ways"]
            if len(hexagon_ways) > 0:
                return random_hexagon
        assert False, "Map.get_random_hexagon_from_area - No hexagon with ways eligible to be selected."

    def get_random_position_from_way(self, sumo_net, way_id, must_be_edge=True):
        assert way_id in self.__ways, "Map.get_random_position_from_way - undefined way"
        way = self.__ways[way_id]
        way_type = way["feature"]["geometry"]["type"]
        assert way_type in ["Point", "LineString"], "Map.get_random_position_from_way- unknown way type"
        way_geometry = way["feature"]["geometry"]
        if must_be_edge:
            if way_type == "Point":
                way_coordinates = way_geometry["coordinates"]
                way_edge = Map.get_sumo_edge_id_from_coordinates(sumo_net, way_coordinates)
                if Map.is_sumo_edge(sumo_net, way_edge) and Map.is_traversable(sumo_net, way_edge):
                    return way_coordinates
                return None
            way_coordinates_list = [*way_geometry["coordinates"]]
            while len(way_coordinates_list) > 0:
                way_coordinates = utils.select_from_list(way_coordinates_list)
                way_coordinates_list.remove(way_coordinates)
                way_edge = Map.get_sumo_edge_id_from_coordinates(sumo_net, way_coordinates)
                if Map.is_sumo_edge(sumo_net, way_edge) and Map.is_traversable(sumo_net, way_edge):
                    return way_coordinates
            return None
        else:
            if way_type == "Point":
                return (way_geometry["coordinates"][0], way_geometry["coordinates"][1])
            return utils.select_from_list(way_geometry["coordinates"])

    @staticmethod
    def get_sumo_current_coordinates(agent_info, agent_type):
        sumo_position = None
        if (agent_type == HumanType.DRIVER):
            sumo_position = traci.vehicle.getPosition(agent_info["id"])
        elif agent_type == HumanType.CUSTOMER:
            sumo_position = traci.person.getPosition(agent_info["id"])
        else:
            raise Exception(f"Map.get_sumo_current_coordinates - Agent type {agent_type} unknown.")

        coordinates = traci.simulation.convertGeo(sumo_position[0], sumo_position[1])
        if not coordinates == (math.inf, math.inf):
            return coordinates
        else:
            print(f"Infinite coordinates for driver {agent_info['id']} - returned current coordinates {agent_info['current_coordinates']}.")
            return agent_info['current_coordinates']


    @staticmethod
    def get_sumo_edge_id_from_coordinates(sumo_net, coordinates):
        id, _, _ = traci.simulation.convertRoad(coordinates[0], coordinates[1], isGeo=True)
        id = re.findall("[\-A-Za-z0-9#]+", id)[0]
        if Map.is_sumo_edge(sumo_net, id):
            edge = sumo_net.getEdge(id)
            return edge.getID()
        elif Map.is_sumo_node(sumo_net, id):
            node = sumo_net.getNode(id)
            outgoings = node.getOutgoing()
            edge = outgoings[0]
            return edge.getID()
        else:
            raise Exception(f"Map.get_sumo_edge_from_coordinates {coordinates} - Impossible to generate edge from coordinates")

    @staticmethod
    def get_sumo_lane_position_from_coordinates(net, coordinates):
        id, pos, _ = traci.simulation.convertRoad(coordinates[0], coordinates[1], isGeo=True)
        id = re.findall("[\-A-Za-z0-9#]+", id)[0]
        if id in list(map(lambda e: e.getID(), net.getEdges())):
            edge = net.getEdge(id)
            edge_length = edge.getLength()
            return pos if pos <= edge_length else edge_length
        elif id in list(map(lambda n: n.getID(), net.getNodes())):
            return 0
        else:
            raise Exception("Map.get_sumo_edge_from_coordinates - Impossible to generate edge from coordinates")

    @staticmethod
    def get_sumo_route_distance(route):
        # check
        return random.randint(3000, 20000)

    @staticmethod
    def get_sumo_route_duration(route):
        # check
        return random.randint(200, 1000)

    def get_way_info(self, way_id):
        return {
            **self.__ways[way_id]
        }

    def increment_generation_probability(self, area_id, agent_type):
        area = self.__areas[area_id]
        assert agent_type in [HumanType.DRIVER, HumanType.CUSTOMER], "Map.increment_generation_probability - unknown agent type"
        agent_label = agent_type.value.lower()
        increment = area["current_generation_probability"][agent_label][1]
        area["current_generation_probability"][agent_label][0] += increment

    @staticmethod
    def is_arrived_by_coordinates(current_coordinates, reference_coordinates, last_distance):
        longitude_distance = current_coordinates[0] - reference_coordinates[0]
        latitude_distance = current_coordinates[1] - reference_coordinates[1]
        if longitude_distance == last_distance[0]:
            if latitude_distance == last_distance[1]:
                return True
        return False

    @staticmethod
    def is_arrived_by_sumo_edge(sumo_net, driver_info):
        if driver_info["state"] in [DriverState.PICKUP, DriverState.ON_ROAD]:
            destination_edge = traci.vehicle.getRoute(driver_info["id"])[-1]
            current_edge = Map.get_sumo_edge_id_from_coordinates(sumo_net, driver_info["current_coordinates"])
            destination_position = driver_info["route"]["destination_position"]
            distance = round(traci.vehicle.getDrivingDistance(driver_info["id"], destination_edge, destination_position))
            if destination_edge == current_edge and distance == 0:
                return True
            return False
        elif driver_info["state"] in [DriverState.IDLE, DriverState.RESPONDING, DriverState.MOVING]:
            current_route_idx = traci.vehicle.getRouteIndex(driver_info["id"])
            driver_route = driver_info["route"]
            current_edge = driver_route[current_route_idx]
            if current_edge == driver_route[-2]:
                return True
            return False

    @staticmethod
    def is_sumo_edge(sumo_net, id):
        return id in list(map(lambda e: e.getID(), sumo_net.getEdges()))

    @staticmethod
    def is_sumo_node(sumo_net, id):
        return id in list(map(lambda n: n.getID(), sumo_net.getNodes()))

    @staticmethod
    def is_traversable(sumo_net, edge_id):
        edge = sumo_net.getEdge(edge_id)
        traversable = edge.allows("private")
        return traversable

    def is_valid_sumo_route(self, sumo_route):
        return len(sumo_route.edges) > 0

    @staticmethod
    def refine_sumo_route(timestamp, from_edge, to_edge, from_point, to_point):
        refined_sumo_route_id, refined_sumo_route = Map.generate_sumo_route_from_edge_ids(from_edge, to_edge)
        refined_sumo_route_distance = refined_sumo_route.length
        refined_sumo_route_duration = refined_sumo_route.travelTime
        return Route(timestamp, from_point, to_point, 'sumo', refined_sumo_route_id, refined_sumo_route.edges, refined_sumo_route_distance, refined_sumo_route_duration)

    def reset_generation_policy(self, area_id):
        area = self.__areas[area_id]
        area["current_generation_policy"] = {
            **area["generation_policy"]
        }

    def update_area_balance(self, area_id, balance):
        area = self.__areas[area_id]
        area["balances"].insert(0, balance)

    def update_area_surge_multiplier(self, area_id, surge_multiplier):
        area = self.__areas[area_id]
        area["surge_multipliers"].insert(0, surge_multiplier)

    def update_generation_policy(self, area_id, generation_policy):
        area = self.__areas[area_id]
        area["generation_policy"] = {
            **generation_policy
        }