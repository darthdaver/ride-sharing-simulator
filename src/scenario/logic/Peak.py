from src.scenario.logic.Scenario import Scenario
from src.state.FileSetup import FileSetup
from src.utils import utils 


class Peak(Scenario):
    def __init__(self):
        super().__init__()
        setup = utils.read_setup(FileSetup.PEAK.value)
        self.peak_intervals = setup["peak_intervals"]
        self.areas_peak_generation_policy_start = setup["areas_generation_policy_peak_start"]
        self.areas_peak_generation_policy_end = setup["areas_generation_policy_peak_end"]

    def trigger_scenario(self, step, net):
        for start, end in self.peak_intervals:
            if (step == start):
                for area_id, area in net.areas.items():
                    area_peak_generation_policy_start = self.areas_peak_generation_policy_start[area_id]
                    area.update_generation_policy(area_peak_generation_policy_start)
                print("PEAK TRIGGERED")

            if (step == end):
                for area_id, area in net.areas.items():
                    area_peak_generation_policy_end = self.areas_peak_generation_policy_end[area_id]
                    area.update_generation_policy(area_peak_generation_policy_end)
                print("PEAK UNTRIGGERED")