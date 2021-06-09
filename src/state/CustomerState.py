from enum import Enum

class CustomerState(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    PICKUP = "PICKUP"
    ONROAD = "ONROAD"