from src.state.DriverState import DriverState
from src.model.Human import Human
from src.utils import utils

import random


class Driver(Human):
    def __init__(self, timestamp, id_num, area_id, num_routes, personality_distribution):
        super().__init__(timestamp, f"driver_{id_num}", area_id, DriverState.IDLE.value, personality_distribution)
        route_num = random.randrange(0, num_routes)
        self.request_pending = False
        self.route_id = f"area_{area_id}_route_{route_num}"
        self.last_ride = timestamp


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


    def receive_request(self):
        self.request_pending = True


    def reject_request(self):
        self.request_pending = False


    def update_pickup_ride(self, ride):
        self.request_pending = False
        self.state = DriverState.PICKUP.value
        self.ride = ride


    def update_onroad_ride(self):
        self.state = DriverState.ONROAD.value


    def update_end_moving(self):
        self.state = DriverState.IDLE.value


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
        driver_str += f"     last ride: {self.last_ride}"
        #driver_str += '-'*6
        #driver_str += '\n'
        return driver_str