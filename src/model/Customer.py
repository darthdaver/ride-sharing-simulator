from src.model.Human import Human
from src.state.CustomerState import CustomerState
from src.utils import utils

import random

class Customer(Human):
    def __init__(self, timestamp, id, state, personality_distribution, coordinates):
        super().__init__(timestamp, id, state, personality_distribution, coordinates)

    def set_coordinates(self, coordinates):
        self.current_coordinates = coordinates
        return self.get_info()

    def set_state(self, state):
        self.state = state
        return self.get_info()

    def update_cancel(self):
        self.state = CustomerState.INACTIVE
        return self.get_info()

    def update_end(self):
        self.state = CustomerState.INACTIVE
        return self.get_info()

    def update_on_road(self):
        self.state = CustomerState.ONROAD
        return self.get_info()

    def update_pending(self):
        self.state = CustomerState.PENDING
        return self.get_info()

    def update_pickup(self):
        self.state = CustomerState.PICKUP
        return self.get_info()

