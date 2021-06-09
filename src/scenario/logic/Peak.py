from src.scenario.logic.Scenario import Scenario
from src.state.FileSetup import FileSetup
from src.utils import utils 


class Peak(Scenario):
    def __init__(self):
        super().__init__()
        setup = utils.read_setup(FileSetup.PEAK.value)
        self.peak_intervals = setup["peak_intervals"]
        pass

    def trigger_scenario(self, step, net):
        for start, end in self.peak_intervals:
            if (step == start):
                net.areas["A"].generation_policy["customer"] = 0.6
                net.areas["B"].generation_policy["customer"] = 0.6
                net.areas["C"].generation_policy["customer"] = 0.4
                net.areas["D"].generation_policy["customer"] = 0.4
                print("PEAK TRIGGERED")

            if (step == end):
                net.areas["A"].generation_policy["customer"] = 0.25
                net.areas["B"].generation_policy["customer"] = 0.25
                net.areas["C"].generation_policy["customer"] = 0.1
                net.areas["D"].generation_policy["customer"] = 0.1
                print("PEAK UNTRIGGERED")