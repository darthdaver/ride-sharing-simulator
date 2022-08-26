from src.state.EventType import EventType

class Scenario:
    def __init__(self, planner):
        self.name = planner["name"]
        self.events = planner["events"]

    def checkEvents(self, timestamp):
        events_type = []
        for ev in self.events:
            if ev["start"] <= timestamp <= ev["end"]:
                if ev["type"] == EventType.HUMAN_PERSONALITY_POLICY.value:
                   events_type.append((EventType.HUMAN_PERSONALITY_POLICY, { **ev["params"], "start": ev["start"] }))
                if ev["type"] == EventType.INCREASE_LENGTH_RIDES.value:
                   events_type.append((EventType.INCREASE_LENGTH_RIDES, { **ev["params"], "start": ev["start"] }))
                if ev["type"] == EventType.GENERATE_TRAFFIC:
                   events_type.append((EventType.GENERATE_TRAFFIC, { **ev["params"], "start": ev["start"] }))
        return events_type