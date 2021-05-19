from src.state.SimulationType import SimulationType
from src.scenario.logic.Scenario import Scenario
from src.scenario.logic.Greedy import Greedy
from src.scenario.logic.Peak import Peak


def dispatch(scenario):
    if (scenario == SimulationType.PEAK):
        return Peak()
    elif (scenario == SimulationType.GREEDY):
        return Greedy()
    else:
        return Scenario()
        

