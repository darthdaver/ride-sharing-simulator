from enum import Enum

class RideRequestState(Enum):
    UNPROCESSED = "UNPROCESSED"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NONE = "NONE"