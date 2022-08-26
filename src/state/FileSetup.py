from enum import Enum

class FileSetup(str, Enum):
    CUSTOMER = "src/config/customer.json"
    DRIVER = "src/config/driver.json"
    SIMULATOR = "src/config/simulator.json"
    PROVIDER = "src/config/provider.json"
    SCENARIO = "src/scenario/planners/drivers_strike.json"
    MAP = "src/repos/city-mapdict-sf_n_o_minimal.json"
    NET = "net_config/san-francisco.net.xml"
    TIMELINE_GENERATION = "data/timeline_gen_events_sf_n_o.json"