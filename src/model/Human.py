from src.utils import utils
import random

class Human:
    def __init__(self, timestamp, id, area_id, personality_distribution):
        self.id = id
        self.area_id = area_id
        self.personality = self.__assign_personality(personality_distribution)
        self.start = timestamp
        self.current_edge = ""
        self.end = -1

    def __assign_personality(self, personality_distribution):
        value = random.random()
        for threshold, personality in personality_distribution:
            if (value <= threshold):
                return personality
        return "normal"

    def __str__(self):
        human_str = ""
        human_str += f"     id: {self.id}\n"
        human_str += f"     area id: {self.area_id}\n"
        human_str += f"     personality: {self.personality}\n"
        human_str += f"     start: {self.id}\n"
        human_str += f"     current edge: {self.id}\n"
        human_str += f"     end: {self.end}\n"
        return human_str

    def accept_ride_choice(self, area, personality_policies):
        surge_multiplier = area.surge_multipliers[-1]
        policy = personality_policies[self.personality]
        for min_surge, max_surge, p in policy:
            if (surge_multiplier >= min_surge and surge_multiplier < max_surge):
                return utils.random_choice(p)
        return utils.random_choice(0.5)