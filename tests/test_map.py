from src.model.Driver import Driver
from src.model.Map import Map
from src.state.DriverState import DriverState
from src.utils import utils
from src.state.FileSetup import FileSetup
from src.settings.Settings import Settings
import traci
import sumolib

env_settings = Settings()
H3_RESOLUTION = env_settings.H3_RESOLUTION

def test_get_edge_id_from_agent():
    net = sumolib.net.readNet(FileSetup.NET)
    driver_personality_policy = [[0.2, "HURRY"], [0.5, "GREEDY"], [1, "NORMAL"]]
    map = Map(utils.read_setup(FileSetup.MAP.value), H3_RESOLUTION)
    coordinates = map.generate_coordinates_from_hexagon(net, "area_1", "random")
    route = Map.generate_random_route_in_area(0, net, coordinates)
    driver = Driver(0, "driver_0", DriverState.IDLE, driver_personality_policy, coordinates, route)
