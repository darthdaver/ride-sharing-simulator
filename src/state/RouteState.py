from enum import Enum

class RouteState(Enum):
    IDLING = "IDLING"
    CHANGE_AREA = "CHANGE_AREA"
    SERVING = "SERVING"