class Scenario:
    def __init__(self, planner):
        self.planner = planner

    def checkEvents(self, timestamp):
        return self.planner[f"{timestamp}"] if f"{timestamp}" in self.planner else None
