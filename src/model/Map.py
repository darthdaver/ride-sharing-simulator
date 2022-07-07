import copy
import math
import random
import re

import h3
from src.utils import utils
from src.state.HumanType import HumanType
from src.model.Route import Route
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
    def compute_distance(current_coordinates, reference_coordinates):
        return (
            abs(current_coordinates[0] - reference_coordinates[0]),
            abs(current_coordinates[1] - reference_coordinates[1])
        )

    def find_near_hexagon(self, hexagon_id):
        hexagon_ring = self.get_near_hexagons(hexagon_id, 20)
        for ring in hexagon_ring:
            for near_hexagon in ring:
                if not self.get_area_from_hexagon(near_hexagon) == "unknown":
                    return Map.get_coordinates_from_hexagon_id(near_hexagon)
        return None

    def generate_coordinates_from_hexagon(self, area_id, hexagon_id="random"):
        area = self.__areas[area_id]
        if hexagon_id == "random":
            hexagons = copy.deepcopy(area["hexagons"])
            while True:
                hexagon_id = utils.select_from_list(hexagons)
                hexagons.remove(hexagon_id)
                hexagon_ways = self.__hexagons[hexagon_id]["ways"]
                if len(hexagon_ways) > 0:
                    break
                assert len(hexagons) > 0, "Map.generate_coordinates_from_hexagon - no way found"

        else:
            assert hexagon_id in area["hexagons"], "Map.generate_coordinates_from_hexagon - Id hexagon dose not belong to area"

        way_id = utils.select_from_list(self.__hexagons[hexagon_id]["ways"])
        position = self.get_random_position_from_way(way_id)
        return position

    def generate_destination_point(self, start_point, distance):
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
                    position_destination = self.get_random_position_from_way(id_destination_way)
                    return position_destination
        assert False, "Map.generate_destination_point - destination not found"
        return start_point

    def generate_destination_point_from_hexagon(self, start_point, destination_hexagon):
        start_hexagon = h3.geo_to_h3(start_point[1], start_point[0], self.__resolution)
        assert destination_hexagon in self.__hexagons, "Map.generate_destination_point_from_hexagon - destination hexagon not found"
        assert len(self.__hexagons[destination_hexagon]["ways"]) > 0 , "Map.generate_destination_point_from_hexagon - destination hexagon has not ways"
        candidate_ways = self.__hexagons[destination_hexagon]["ways"]
        id_destination_way = utils.select_from_list(candidate_ways)
        position_destination = self.get_random_position_from_way(id_destination_way)
        return position_destination

    def generate_random_route_in_area(self, timestamp, sumo_net, start_point):
        area_id = self.get_area_from_coordinates(start_point)
        start_hexagon = self.get_hexagon_id_from_coordinates(start_point)
        destination_hexagon = self.get_random_hexagon_from_area(area_id, exclude_hexagons=[start_hexagon])
        destination_point = self.generate_destination_point_from_hexagon(start_point, destination_hexagon)
        random_route = self.generate_route_from_coordinates(timestamp, sumo_net, [start_point, destination_point])
        return random_route

    @staticmethod
    def generate_route_from_coordinates(timestamp, sumo_net, waypoints):
        from_edge_id = Map.get_sumo_edge_id_from_coordinates(sumo_net, waypoints[0])
        to_edge_id = Map.get_sumo_edge_id_from_coordinates(sumo_net, waypoints[1])
        sumo_route = traci.simulation.findRoute(from_edge_id, to_edge_id)
        sumo_route_distance = sumo_route.length
        sumo_route_duration = sumo_route.travelTime
        sumo_route_id = f"route_from_{from_edge_id}_to_{to_edge_id}"
        if len(sumo_route.edges) > 0:
            traci.route.add(sumo_route_id, sumo_route.edges)
            return Route(timestamp, waypoints[0], waypoints[1], "sumo", sumo_route_id, sumo_route, sumo_route_distance, sumo_route_duration)
        else:
            error_msg =f"Map.generate_route_from_coordinates - Route impossible: no connection between the source {waypoints[0]} and the desitnation {waypoints[1]}."
            print(error_msg)
            raise Exception(error_msg)

    @staticmethod
    def generate_sumo_route_from_edge_ids(from_edge_id, to_edge_id):
        sumo_route = traci.simulation.findRoute(from_edge_id, to_edge_id)
        sumo_route_id = f"route_from_{from_edge_id}_to_{to_edge_id}"
        if len(sumo_route.edges) > 0:
            traci.route.add(sumo_route_id, sumo_route.edges)
            return (sumo_route_id, sumo_route)
        else:
            error_msg = f"Map.generate_route_from_coordinates - Route impossible: no connection between the source {waypoints[0]} and the desitnation {waypoints[1]}."
            print(error_msg)
            raise Exception(error_msg)

    def get_area_from_coordinates(self, coordinates):
        hexagon_id = h3.geo_to_h3(coordinates[1], coordinates[0], self.__resolution)
        if not self.__hexagons[hexagon_id]:
            return "unknown"
        area_id = self.__hexagons[hexagon_id]["area_id"]
        return area_id

    def get_area_from_hexagon(self, hexagon_id="random"):
        if not self.__hexagons[hexagon_id]:
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

    def get_random_position_from_way(self, way_id):
        assert way_id in self.__ways, "Map.get_random_position_from_way - undefined way"
        way = self.__ways[way_id]
        way_type = way["feature"]["geometry"]["type"]
        assert way_type in ["Point", "LineString"], "Map.get_random_position_from_way- unknown way type"
        if way_type == "Point":
            way_geometry = way["feature"]["geometry"]
            return (way_geometry["coordinates"][0], way_geometry["coordinates"][1])
        way_geometry = way["feature"]["geometry"]
        return utils.select_from_list(way_geometry["coordinates"])

    @staticmethod
    def get_sumo_edge_id_from_coordinates(net, coordinates):
        id, _, _ = traci.simulation.convertRoad(coordinates[0], coordinates[1], isGeo=True)
        id = re.findall("[\-A-Za-z0-9#]+", id)[0]
        if id in list(map(lambda e: e.getID(), net.getEdges())):
            edge = net.getEdge(id)
            return edge.getID()
        elif id in list(map(lambda n: n.getID(), net.getNodes())):
            node = net.getNode(id)
            outgoings = node.getOutgoing()
            edge = outgoings[0]
            return edge.getID()
        else:
            raise Exception("Map.get_sumo_edge_from_coordinates - Impossible to generate edge from coordinates")

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
    def is_arrived_by_sumo_edge(driver_id):
        destination_edge = traci.vehicle.getRoute(driver_id)[-1]
        distance = traci.vehicle.getDrivingDistance(driver_id, destination_edge, 0)
        if distance <= 0:
            return True
        return False

    def is_valid_sumo_route(self, sumo_route):
        return len(sumo_route.edges) > 0

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