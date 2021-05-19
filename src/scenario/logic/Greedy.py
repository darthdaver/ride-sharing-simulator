from src.scenario.logic.Scenario import Scenario
from src.state.FileSetup import FileSetup
from src.utils import utils 

class Greedy(Scenario):
    def __init__(self):
        super().__init__()
        setup = utils.read_setup(FileSetup.GREEDY.value)
        self.trigger_step = setup["trigger_step"]
        pass

    def thrown_scenario(self, step, net):
        if (self.trigger_step == step):
            net.areas["A"].generation["customer"] = 0.8
            net.areas["A"].generation["many"] = (8, 3)
            print("GREEDY TRIGGERED")