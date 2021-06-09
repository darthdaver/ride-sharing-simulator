from src.state.SimulationType import SimulationType
from src.scenario.logic.Scenario import Scenario
from src.scenario.logic.Greedy import Greedy
from src.scenario.logic.Peak import Peak


def dispatch(scenario):
    if (scenario.upper() == SimulationType.PEAK.value):
        return Peak()
    elif (scenario.upper() == SimulationType.GREEDY.value):
        return Greedy()
    else:
        return Scenario()
        

