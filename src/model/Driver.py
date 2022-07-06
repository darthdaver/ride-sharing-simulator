from src.model.Human import Human
from src.state.DriverState import DriverState

class Driver(Human):
    def __init__(self, timestamp, id, state, personality_distribution, coordinates):
        super().__init__(timestamp, id, state, personality_distribution, coordinates)
        self.__route = None
        self.__current_distance = None
        self.__last_ride_timestamp = timestamp
        self.__pending_request = False

    def get_info(self):
        return {
            **super().get_info(),
            "pending_request": self.__pending_request,
            "route": None if self.__route is None else self.__route.to_dict(),
            "last_ride_timestamp": self.__last_ride_timestamp,
            "current_distance": self.__current_distance
        }

    def receive_request(self):
        self.state = DriverState.RESPONDING
        self.__pending_request = True
        return self.get_info()

    def reject_request(self):
        self.__pending_request = False
        self.state = DriverState.IDLE
        return self.get_info()

    def set_current_distance(self, current_distance):
        self.__current_distance = current_distance
        return self.get_info()

    def set_coordinates(self, coordinates):
        self.current_coordinates = coordinates
        return self.get_info()

    def set_pending_request(self, value):
        self.__pending_request = value
        return self.get_info()

    def set_route(self, route):
        self.__route = route
        return self.get_info()

    def set_state(self, state):
        self.state = state
        return self.get_info()

    def update_cancel(self):
        pass

    def update_end(self, timestamp):
        self.state = DriverState.IDLE
        self.__route = None
        self.__last_ride_timestamp = timestamp
        return self.get_info()

    def update_end_moving(self):
        self.state = DriverState.IDLE
        self.__route = None
        return self.get_info()

    def update_on_road(self, destination_route):
        self.__route = destination_route
        self.state = DriverState.ONROAD
        return self.get_info()

    def update_pickup(self, route):
        self.state = DriverState.PICKUP
        self.__pending_request = False
        self.__route = route
        return self.get_info()
    