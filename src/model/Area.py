from src.utils import utils

class Area:
    def __init__(self, area):
        self.id = area["id"]
        self.edges = area["edges"]
        self.generation_policy = area["generation"]
        self.surge_multiplier = 1
        self.customers = []
        self.drivers = []
        self.customer_personality_distribution = area["customer_personality_probability_distribution"]
        self.driver_personality_distribution = area["driver_personality_probability_distribution"]
        self.stats = {
            "canceled": 0,
            "completed": 0,
            "balances": [],
            "surge_multipliers": [],
            "prices": [],
            "expected_prices": [],
            "waiting_times": [],
            "ride_times": [],
            "total_times": [],
            "waiting_lengths": [],
            "ride_lengths": [],
            "total_lengths": [],
            "diff_prices": [],
            "diff_waiting_times": [],
            "diff_total_times": [],
            "diff_ride_times": [],
            "diff_waiting_lengths": [],
            "diff_ride_lengths": [],
            "diff_total_lengths": [],
            "rejections": [],
            "last_checkpoint": 0
        }


    def remove_driver(self, driver_id):
        self.drivers.remove(driver_id)


    def update_cancel_ride(self, customer_id):
        self.customers.remove(customer_id)
        self.stats["canceled"] += 1

    
    def update_end_ride(self, ride):
        self.customers.remove(ride.customer_id)
        self.stats["completed"] += 1
        self.stats["waiting_times"].append(ride.stats["waiting_time"])
        self.stats["ride_times"].append(ride.stats["ride_time"])
        self.stats["total_times"].append(ride.stats["total_time"])
        self.stats["waiting_lengths"].append(ride.stats["waiting_length"])
        self.stats["ride_lengths"].append(ride.stats["ride_length"])
        self.stats["total_lengths"].append(ride.stats["total_time"])
        self.stats["expected_prices"].append(ride.stats["expected_price"])
        self.stats["prices"].append(ride.stats["price"])
        self.stats["diff_prices"].append(ride.stats["price"] - ride.stats["expected_price"])
        self.stats["diff_waiting_times"].append(ride.stats["waiting_time"] - ride.stats["expected_waiting_time"])
        self.stats["diff_ride_times"].append(ride.stats["ride_time"] - ride.stats["expected_ride_time"])
        self.stats["diff_total_times"].append(ride.stats["total_time"] - ride.stats["expected_total_time"])
        self.stats["diff_waiting_lengths"].append(ride.stats["waiting_length"] - ride.stats["expected_waiting_length"])
        self.stats["diff_ride_lengths"].append(ride.stats["ride_length"] - ride.stats["expected_ride_length"])
        self.stats["diff_total_lengths"].append(ride.stats["total_length"] - ride.stats["expected_total_length"])
        self.stats["rejections"].append(ride.stats["rejections"])



    def __str__(self):
        area_str = '*'*6
        area_str += f"\nAREA {self.id}\n"
        area_str += '*'*6
        area_str += '\n'
        area_str += f"min edge id: +-{self.edges[0]}\n"
        area_str += f"max edge id: +-{self.edges[1]}\n"
        area_str += f"generation policy: [\n"
        area_str += f"  - customer: {self.generation_policy['customer']}\n"
        area_str += f"  - driver: {self.generation_policy['driver']}\n"
        area_str += f"  - many: {self.generation_policy['many']}\n"
        area_str += f"surge multiplier: {self.surge_multiplier}\n"
        area_str += f"balance: {self.stats['balances'][-1]}\n"
        area_str += f"customers: ["
        if (len(self.customers) > 0):
            area_str += "\n"
            for idx, customer in enumerate(self.customers, start=1):
                if not (idx == len(self.customers)):
                    area_str += f"   {customer},\n"
                else:
                    area_str += f"   {customer}\n"
                    area_str += "]\n"
        else:
            area_str += " ]\n"
        area_str += f"drivers: ["
        if (len(self.drivers) > 0):
            area_str += "\n"
            for idx, driver in enumerate(self.drivers, start=1):
                if not (idx == len(self.drivers)):
                    area_str += f"   {driver},\n"
                else:
                    area_str += f"   {driver}\n"
                    area_str += "]\n"
        else:
            area_str += " ]\n"
        area_str += f"active customers: {len(self.customers)}\n"
        area_str += f"active drivers: {len(self.drivers)}\n"

        for k,v in self.stats.items():
            label = k.replace("_"," ")
            if (isinstance(v,list)):
                area_str += f"average {label}: {utils.list_average(v)}\n"
            else:
                area_str += f"{label}: {v}\n"
        return area_str