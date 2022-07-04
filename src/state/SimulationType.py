from enum import Enum

class SimulationType(str, Enum):
    NORMAL = "NORMAL"
    PEAK = "PEAK"
    GREEDY = "GREEDY"