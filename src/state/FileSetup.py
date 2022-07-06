from enum import Enum

class FileSetup(str, Enum):
    CUSTOMER = "src/config/customer.json"
    DRIVER = "src/config/driver.json"
    SIMULATOR = "src/config/simulator.json"
    PROVIDER = "src/config/provider.json"
    SCENARIO = "src/config/scenario.json"
    TUNING = "src/config/tuning.json"
    MAP = "src/repos/city-mapdict.json"
    NET = "net_config/san-francisco.net.xml"
