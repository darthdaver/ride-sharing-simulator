from src.model.Human import Human
from src.state.DriverState import DriverState

class Driver(Human):
    def __init__(self, timestamp, id, state, personality_distribution, coordinates, route):
        super().__init__(timestamp, id, state, personality_distribution, coordinates)
        self.__route = route
        self.__current_distance = None
        self.__last_ride_timestamp = timestamp
        self.__rides_completed = 0

    def get_info(self):
        return {
            **super().get_info(),
            "route": None if self.__route is None else self.__route.to_dict(),
            "last_ride_timestamp": self.__last_ride_timestamp,
            "current_distance": self.__current_distance,
            "rides_completed": self.__rides_completed
        }

    def receive_request(self):
        self.state = DriverState.RESPONDING
        return self.get_info()

    def reject_request(self):
        self.state = DriverState.IDLE
        return self.get_info()

    def set_current_distance(self, current_distance):
        self.__current_distance = current_distance
        return self.get_info()

    def set_coordinates(self, coordinates):
        self.current_coordinates = coordinates
        return self.get_info()

    def set_route(self, route):
        self.__route = route
        return self.get_info()

    def set_route_destination_position(self, destination_position):
        self.__route.set_destination_position(destination_position)

    def set_state(self, state):
        self.state = state
        return self.get_info()

    def update_cancel(self):
        pass

    def update_end(self, timestamp, route):
        self.state = DriverState.IDLE
        self.__route = route
        self.__last_ride_timestamp = timestamp
        self.__rides_completed += 1
        return self.get_info()

    def update_end_moving(self, route):
        self.state = DriverState.IDLE
        self.__route = route
        return self.get_info()

    def update_on_road(self, destination_route):
        self.__route = destination_route
        self.state = DriverState.ON_ROAD
        return self.get_info()

    def update_pickup(self, route):
        self.state = DriverState.PICKUP
        self.__route = route
        return self.get_info()
    