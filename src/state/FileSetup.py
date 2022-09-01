from enum import Enum

class FileSetup(str, Enum):
    CUSTOMER = "src/config/customer.json"
    DRIVER = "src/config/driver.json"
    SIMULATOR = "src/config/simulator.json"
    PROVIDER = "src/config/provider.json"
    SCENARIO = "src/scenario/planners/normal.json"
    MAP = "src/repos/city-mapdict-sf_n_o_minimal.json"
    TAZ_EDGES = "data/sf_n_o_minimal_mov_edges_dict.json"
    NET = "net_config/sf_minimal.net.xml"
    TIMELINE_GENERATION = "data/timeline_gen_events_sf_n_o.json"