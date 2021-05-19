from enum import Enum

class RideState(Enum):
    REQUESTED = "REQUESTED"
    PENDING = "PENDING"
    PICKUP = "PICKUP"
    ONROAD = "ONROAD"
    END = "END"
    CANCELED = "CANCELED"