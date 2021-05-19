from enum import Enum

class FileSetup(Enum):
    CUSTOMER = "src/repo/customer.json"
    DRIVER = "src/repo/driver.json"
    NET = "src/repo/net.json"
    SIMULATOR = "src/repo/simulator.json"
    UBER = "src/repo/uber.json"
    GREEDY = "src/scenario/setup/greedy.json"
    PEAK = "src/scenario/setup/peak.json"