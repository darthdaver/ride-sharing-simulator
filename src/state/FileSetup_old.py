from enum import Enum

class FileSetup(str, Enum):
    CUSTOMER = "src/config/customer.json"
    DRIVER = "src/config/driver.json"
    NET = "src/config/net.json"
    SIMULATOR = "src/config/simulator.json"
    UBER = "src/config/uber.json"
    GREEDY = "src/scenario/setup/greedy.json"
    PEAK = "src/scenario/setup/peak.json"