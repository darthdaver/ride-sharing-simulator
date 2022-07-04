from enum import Enum

class RouteState(str, Enum):
    IDLING = "IDLING"
    CHANGE_AREA = "CHANGE_AREA"
    SERVING = "SERVING"