from src.state.RideState import RideState
from src.state.RideRequestState import RideRequestState


class Ride:
    def __init__(self, id, customer_id, meeting_point, destination_point):
        self.__id = id
        self.__customer_id = customer_id
        self.__driver_id = None
        self.__meeting_point = meeting_point
        self.__destination_point = destination_point
        self.__state = RideState.REQUESTED
        self.__request = {
            "state": RideRequestState.UNPROCESSED,
            "drivers_candidates": [],
            "rejections": [],
            "current_candidate": None
        }
        self.__routes = {
            "meeting_route": None,
            "destination_route": None
        }
        self.__stats = {}

    def add_driver_candidate(self, driver_candidate):
        self.__request["drivers_candidates"].append(driver_candidate)

    def decrement_count_down_request(self):
        assert self.__request["current_candidate"] is not None, "Ride.decrement_count_down_request - candidate is undefined."
        if self.__request["current_candidate"]:
            self.__request["current_candidate"]["response_count_down"] -= 1

    def get_destination_route(self):
        return self.__routes["destination_route"]

    def get_id(self):
        return self.__id

    def get_info(self):
        return {
            "id": self.__id,
            "customer_id": self.__customer_id,
            "driver_id": self.__driver_id,
            "meeting_point": self.__meeting_point,
            "destination_point": self.__destination_point,
            "request": {
                **self.__request
            },
            "routes": self.routes_to_dict(),
            "state": self.__state,
            "stats": {
                **self.__stats
            }
        }

    def get_meeting_route(self):
        return self.__routes["meeting_route"]

    def refine_route(self, route_type, route):
        self.__routes[route_type] = route
        return self.get_info()

    def request_canceled(self):
        self.__request["state"] = RideRequestState.CANCELED
        self.__state = RideState.CANCELED
        return self.get_info()

    def request_rejected(self, driver_id, idle_driver=True):
        if idle_driver:
            self.__request["rejections"].append(driver_id)
        self.__request["state"] = RideRequestState.REJECTED
        return self.get_info()

    def routes_to_dict(self):
        return {
            "meeting_route": None if self.__routes["meeting_route"] is None else self.__routes["meeting_route"].to_dict(),
            "destination_route": None if self.__routes["destination_route"] is None else self.__routes["destination_route"].to_dict()
        }

    def set_candidate(self, candidate):
        self.__request["current_candidate"] = candidate
        assert candidate in self.__request["drivers_candidates"], "Ride.set_candidate - candidate is not included in drivers candidates"
        self.__request["drivers_candidates"] = list(filter(lambda d: not d["id"] == candidate["id"], self.__request["drivers_candidates"]))
        return self.get_info()

    def set_driver(self, driver_id):
        self.__driver_id = driver_id
        return self.get_info()

    def set_request_state(self, state):
        self.__request["state"] = state
        return self.get_info()

    def set_state(self, state):
        self.__state = state
        return self.get_info()

    def sort_candidates(self):
        self.__request["drivers_candidates"] = sorted(self.__request["drivers_candidates"], key=lambda d: d["expected_duration"])

    def update_cancel(self):
        pass

    def update_end(self, stats):
        self.__state = RideState.END
        self.__set_stats(stats)
        return self.get_info()

    def update_on_road(self, stats):
        self.__state = RideState.ON_ROAD
        self.__set_stats(stats)
        return self.get_info()

    def update_pending(self, timestamp):
        self.__state = RideState.PENDING
        self.__stats["timestamp_request"] = timestamp
        return self.get_info()

    def update_accepted(self, driver_id, meeting_route, destination_route, stats):
        self.__driver_id = driver_id
        self.__set_route("meeting", meeting_route)
        self.__set_route("destination", destination_route)
        self.__set_stats(stats)
        self.__request["state"] = RideRequestState.ACCEPTED
        return self.get_info()

    def update_pickup(self):
        self.__state = RideState.PICKUP
        return self.get_info()

    def __set_route(self, route_type, route):
        if route_type == "meeting":
            self.__routes["meeting_route"] = route
        if route_type == "destination":
            self.__routes["destination_route"] = route
        return self.get_info()

    def __set_stats(self, stats):
        self.__stats = {
            **self.__stats,
            **stats
        }
        return self.get_info()

