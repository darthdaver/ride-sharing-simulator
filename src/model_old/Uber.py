from src.state.RideState import RideState
from src.utils import utils

class Uber:
    def __init__(self, fare, request):
        self.base_fare = fare["base_fare"]
        self.minimum_fare = fare["minimum_fare"]
        self.fee_per_minute = fare["fee_per_minute"]
        self.fee_per_mile = fare["fee_per_mile"]
        self.surge_multiplier_policy = fare["surge_multiplier_policy"]
        self.request_max_driver_distance = request["max_driver_distance"]
        self.customers = {}
        self.drivers = {}
        self.rides = {}
        self.unprocessed_requests = []
        self.pending_requests = []
        self.pickup_rides = []
        self.onroad_rides = []
        self.ended_rides = []
        self.canceled_rides = []
        self.idle_drivers = []
        self.pickup_drivers = []
        self.onroad_drivers = []
        self.inactive_drivers = []
        self.matched_rides = []


    # computed expected price of the ride
    def compute_price(self, travel_time, ride_length, surge_price_multiplier):
        #print("compute_price")
        price = (self.base_fare + (self.fee_per_minute * travel_time) + (self.fee_per_mile * ride_length/1000)) * surge_price_multiplier
        return price


    def get_all_rides(self):
        all_rides = [
            self.unprocessed_requests,
            self.pending_requests,
            self.pickup_rides,
            self.onroad_rides,
            self.ended_rides,
            self.canceled_rides
        ]
        if not (self.__check_empty_intersection(all_rides)):
            raise Exception("Unexpected not empty intersection")
        return utils.lists_union(all_rides)


    def get_rides_in_progress(self):
        in_progress_rides = [
            self.pickup_rides,
            self.onroad_rides
        ]
        if not (self.__check_empty_intersection(in_progress_rides)):
            raise Exception("Unexpected not empty intersection")
        return utils.lists_union(in_progress_rides)


    def print_matched_rides(self):
        print("[\n")
        for c, d, r, t in self.matched_rides:
            print(f"    {c} - {d} - {r}")
        print("]\n")


    def print_ride_list(self, ride_list):
        print("[\n")
        for ride in ride_list:
            print(f"    {ride.id}")
        print("]\n")

    def print_driver_list(self, driver_list):
        print("[\n")
        for driver in driver_list:
            print(f"    {driver.id}")
        print("]\n")


    def receive_request(self, ride_request, customer):
        self.unprocessed_requests.append(ride_request)
        self.rides[customer.id] = ride_request


    def update_cancel_ride(self, ride):
        if (ride in self.unprocessed_requests):
            self.unprocessed_requests.remove(ride)
        elif (ride in self.pending_requests):
            self.pending_requests.remove(ride)
        self.canceled_rides.append(ride)


    def update_end_ride(self, ride, driver):
        self.onroad_rides.remove(ride)
        self.ended_rides.append(ride)
        self.onroad_drivers.remove(driver)
        self.idle_drivers.append(driver)


    def update_onroad_ride(self, ride, driver):
        self.inactive_drivers
        self.pickup_drivers.remove(driver)
        self.onroad_drivers.append(driver)
        self.pickup_rides.remove(ride)
        self.onroad_rides.append(ride)
    

    def update_pending_request(self, ride):
        if (ride in self.unprocessed_requests):
            self.unprocessed_requests.remove(ride)
        self.pending_requests.append(ride)


    def update_pickup_ride(self, timestamp, ride, driver, customer):
        self.idle_drivers.remove(driver)
        self.pickup_drivers.append(driver)
        self.pending_requests.remove(ride)
        self.pickup_rides.append(ride)
        self.matched_rides.append((customer.id, driver.id, ride.id, timestamp))


    def update_remove_driver(self, driver):
        self.idle_drivers.remove(driver)
        self.inactive_drivers.append(driver)


    def __str__(self):
        uber_str = '-'*4
        uber_str += "\nUBER\n"
        uber_str += '-'*4
        uber_str += '\n'
        uber_str += f"request max driver distance: {self.request_max_driver_distance}\n"
        uber_str += "fare:\n"
        uber_str += f"     - base_fare: {self.base_fare}\n"
        uber_str += f"     - minimum fare: {self.minimum_fare}\n"
        uber_str += f"     - fee per minute: {self.fare_per_minute}\n"
        uber_str += f"     - fee per mile: {self.fee_per_mile}\n"
        uber_str += f"surge multiplier:\n"
        for min_surge, max_surge, increment in self.surge_multiplier_policy:
            uber_str += f"     - [{min_surge},{max_surge}] --> {increment}\n"

        uber_str += "customers: ["
        if (len(self.customers.items()) > 0):
            uber_str += "\n"
            for idx, customer in enumerate(self.customers, start=1):
                if not (idx == len(self.customers)):
                    uber_str += str(customer[1]) + ",\n\n"
                else:
                    uber_str += str(customer[1])
                    uber_str += "\n]\n"
        else:
            uber_str += " ]\n"
        
        uber_str += "drivers: ["
        if (len(self.drivers) > 0):
            uber_str += "\n"
            for idx, driver in enumerate(self.drivers, start=1):
                if not (idx == len(self.drivers)):
                    uber_str += str(driver[1]) + ",\n\n"
                else:
                    uber_str += str(driver[1])
                    uber_str += "\n]\n"
        else:
            uber_str += " ]\n"

        uber_str += '-'*4
        uber_str += '\n'
        return uber_str