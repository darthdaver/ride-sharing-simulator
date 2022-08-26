from src.state.EventType import EventType

class Scenario:
    def __init__(self, planner):
        self.name = planner["name"]
        self.events = planner["events"]

    def check_events(self, timestamp):
        timestamp = int(timestamp)
        events_type = []
        for ev in self.events:
            if ev["start"] <= timestamp < ev["end"]:
                if timestamp == ev["start"]:
                    print(f"TRIGGER {ev['type']}: START")
                if ev["type"] == EventType.HUMAN_PERSONALITY_POLICY.value:
                    print("TRIGGER")
                    events_type.append((EventType.HUMAN_PERSONALITY_POLICY, { **ev["params"], "start": ev["start"] }))
                if ev["type"] == EventType.INCREASE_LENGTH_RIDES.value:
                    events_type.append((EventType.INCREASE_LENGTH_RIDES, { **ev["params"], "start": ev["start"] }))
                if ev["type"] == EventType.GENERATE_TRAFFIC.value:
                    events_type.append((EventType.GENERATE_TRAFFIC, { **ev["params"], "start": ev["start"] }))
                if ev["type"] == EventType.DRIVERS_STRIKE.value:
                    events_type.append((EventType.DRIVERS_STRIKE, { **ev["params"], "start": ev["start"] }))
            if timestamp == ev["end"]:
                print(f"TRIGGER {ev['type']}: END")
        return events_type