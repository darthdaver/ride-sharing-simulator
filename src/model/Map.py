import copy
import math
import random
import h3
from src.utils import utils
from src.state.HumanType import HumanType
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
        start_hexagon = h3.geo_to_h3(start_point[0], start_point[1], self.__resolution)
        ring_distance = distance - math.floor(random.random() * 2)
        if ring_distance < 1:
            print(ring_distance)
        candidate_hexagons = h3.k_ring_distances(start_hexagon, ring_distance)
        for i in range(ring_distance, 0, -1):
            ring_candidates = candidate_hexagons[i]
            found = False
            while (len(ring_candidates) > 0 and not found):
                id_destination_hexagon = ring_candidates.pop(math.floor(random.random() * len(ring_candidates)))[0]
                assert id_destination_hexagon is not None, "Map.generate_destination_point - Id destination hexagon is undefined"
                if self.__hexagons[id_destination_hexagon] is not None:
                    found = True
                    candidate_ways = self.__hexagons[id_destination_hexagon]["ways"]
                    id_destination_way = utils.select_from_list(candidate_ways)
                    position_destination = self.get_random_position_from_way(id_destination_way)
                    return position_destination
        assert False, "Map.generate_destination_point - destination not found"
        return start_point

    def generate_sumo_route_from_coordinates(self, waypoints):
        pass

    def get_area_from_coordinates(self, coordinates):
        hexagon_id = h3.geo_to_h3(coordinates[0], coordinates[1], self.__resolution)
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
        return (h3_coordinates[0], h3_coordinates[1])

    def get_hexagon_id_from_coordinates(self, coordinates):
        return h3.geo_to_h3(coordinates[0], coordinates[1], self.__resolution)

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
    def get_sumo_route_distance(self, route):
        pass

    @staticmethod
    def get_sumo_route_duration(self, route):
        pass

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
    def is_arrived(current_coordinates, reference_coordinates, last_distance):
        longitude_distance = current_coordinates[0] - reference_coordinates[0]
        latitude_distance = current_coordinates[1] - reference_coordinates[1]
        if longitude_distance == last_distance["longitude_distance"]:
            if latitude_distance == last_distance["latitude_distance"]:
                return True
        return False

    def reset_generation_policy(self, area_id):
        area = self.__areas[area_id]
        area["current_generation_policy"] = {
            **area["generation_policy"]
        }

    @staticmethod
    def sumo_edge_from_coordinates(coordinates):
        print(3)
        print(coordinates)
        return traci.simulation.convertRoad(coordinates[0], coordinates[1], isGeo=True)

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