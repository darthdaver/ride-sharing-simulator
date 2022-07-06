from src.utils import utils
from src.state import CustomerState, DriverState
import random
import copy
import traci

class Human:
    def __init__(self, timestamp, id, state, personality_distribution, coordinates):
        self._id = id
        self._state = state
        self._timestamp = timestamp
        self._personality = self.__assign_personality(personality_distribution)
        self._current_coordinates = coordinates

    @property
    def id(self):
        return self._id

    @property
    def current_coordinates(self):
        return self._current_coordinates

    @current_coordinates.setter
    def current_coordinates(self, coordinates):
        self._current_coordinates = coordinates


    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def get_info(self):
        return {
            "current_coordinates": self._current_coordinates,
            "id": self._id,
            "personality": self._personality,
            "state": self._state,
            "timestamp": self._timestamp
        }

    def __assign_personality(self, personality_distribution):
        value = random.random()

        for treshold, personality in personality_distribution:
            if value <= treshold:
                return personality
        return "normal"

    def accept_ride_conditions(self, surge_multiplier, policy, bias=0):
        for min_surge, max_surge, probability in policy:
            if min_surge <= surge_multiplier < max_surge:
                return utils.random_choice(probability + bias)
        return utils.random_choice(0.5 + bias)

