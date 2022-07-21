from enum import Enum

class DriverState(str, Enum):
    RESPONDING = "RESPONDING"
    INACTIVE = "INACTIVE"
    IDLE = "IDLE"
    MOVING = "MOVING"
    PICKUP = "PICKUP"
    ON_ROAD = "ON_ROAD"