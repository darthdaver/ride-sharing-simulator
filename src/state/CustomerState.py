from enum import Enum

class CustomerState(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    PICKUP = "PICKUP"
    ON_ROAD = "ON_ROAD"