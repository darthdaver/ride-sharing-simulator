from enum import Enum

class FileSetup(str, Enum):
    CUSTOMER = "src/config/customer.json"
    DRIVER = "src/config/driver.json"
    SIMULATOR = "src/config/simulator.json"
    PROVIDER = "src/config/provider.json"
    SCENARIO = "src/config/scenario.json"
    MAP = "src/repos/city-mapdict.json"
    NET = "net_config/schaffhausen_simplified.net.xml"
