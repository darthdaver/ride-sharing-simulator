class Route:
    def __init__(self, timestamp, starting_point, destination_point, route_type, route, original_distance, original_duration):
        self.__timestamp = timestamp
        self.__starting_point = starting_point
        self.__destination_point = destination_point
        self.__route_type = route_type
        self.__route = route
        self.__original_distance = original_distance
        self.__original_duration = original_duration

    def get_starting_point(self):
        return self.__starting_point

    def get_destination_point(self):
        return self.__destination_point

    def get_route_type(self):
        return self.__route_type

    def get_route(self):
        return self.__route

    def get_otiginal_distance(self):
        return self.__original_distance

    def get_original_duration(self):
        return self.__original_duration

    def get_timestamp(self):
        return self.__timestamp

    def to_dict(self):
        return {
            "starting_point": self.__starting_point,
            "destination_point": self.__destination_point,
            "route_type": self.__route_type,
            "route": self.__route
        }