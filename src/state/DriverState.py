from enum import Enum

class DriverState(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    IDLE = "IDLE"
    MOVING = "MOVING"
    PICKUP = "PICKUP"
    ONROAD = "ONROAD"