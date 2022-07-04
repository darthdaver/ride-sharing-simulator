from enum import Enum

class RideState(str, Enum):
    REQUESTED = "REQUESTED"
    PENDING = "PENDING"
    PICKUP = "PICKUP"
    ONROAD = "ONROAD"
    END = "END"
    CANCELED = "CANCELED"
    NOT_ACCOMPLISHED = "NOT ACCOMPLISHED"
