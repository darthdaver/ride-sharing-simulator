from src.state.DriverState import DriverState
from src.model.Human import Human
from serc.utils import utils

import random


class Driver(Human):
    def __init__(self, timestamp, id_num, area_id, num_routes, personality_distribution):
        super().__init__(timestamp, f"driver_{id_num}", area_id, personality_distribution)
        route_num = random.randrange(0, num_routes)
        self.route_id = f"area_{area_id}_route_{route_num}"
        self.state = DriverState.IDLE.value
        self.last_ride = timestamp
        self.ride_stats = {}


    def generate_from_to(self, edge_prefix, edges):
        min_edge = edges[0]
        max_edge = edges[1]
        from_edge = self.current_edge
        to_edge_num = random.randrange(min_edge, max_edge + 1)
        prefix_to = "" if utils.random_choice(0.5) else "-"
        to_edge = f"{prefix_to}{edge_prefix}{to_edge_num}"
        return (from_edge, to_edge)
        
    def remove(self, timestamp):
        self.state = DriverState.INACTIVE.value
        self.end = timestamp

    def update_end_ride(self, timestamp):
        self.state = DriverState.IDLE.value
        self.last_ride = timestamp


    def __str__(self):
        #driver_str = '-'*6
        #driver_str += "\nDRIVER\n"
        #driver_str += '-'*6
        #driver_str += '\n'
        driver_str = ""
        driver_str += super().__str__()
        driver_str += f"     route id: {self.route_id}\n"
        driver_str += f"     state: {self.state}\n"
        driver_str += f"     last ride: {self.last_ride}"
        #driver_str += '-'*6
        #driver_str += '\n'
        return driver_str