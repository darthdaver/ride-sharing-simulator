from src.scenario.logic.Scenario import Scenario
from src.state.FileSetup import FileSetup
from src.utils import utils 

class Greedy(Scenario):
    def __init__(self):
        super().__init__()
        setup = utils.read_setup(FileSetup.GREEDY.value)
        self.greedy_interval = setup["greedy_interval"]
        self.areas_greedy_generation_policy_start = setup["areas_generation_policy_greedy_start"]
        self.areas_greedy_generation_policy_end = setup["areas_generation_policy_greedy_end"]

    def trigger_scenario(self, step, net):
        start, end = self.greedy_interval
        if (step == start):
            for area_id, area in net.areas.items():
                area_greedy_generation_policy_start = self.areas_greedy_generation_policy_start[area_id]
                area.update_generation_policy(area_greedy_generation_policy_start)
            print("GREEDY TRIGGERED")

        if (step == end):
            for area_id, area in net.areas.items():
                area_greedy_generation_policy_end = self.areas_greedy_generation_policy_end[area_id]
                area.update_generation_policy(area_greedy_generation_policy_end)
            print("GREEDY UNTRIGGERED")