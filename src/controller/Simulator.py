from time import time
from src.model.Customer import Customer
from src.model.Driver import Driver
from src.model.Net import Net
from src.model.Uber import Uber
from src.model.Ride import Ride
from src.state.RideState import RideState
from src.state.DriverState import DriverState
from src.state.FileSetup import FileSetup
from src.state.SimulationType import SimulationType
from src.utils import utils 
from src.scenario import dispatch_scenario

import random
import sys


class Simulator:
    def __init__(self, traci):
        self.traci = traci

        customer_setup = utils.read_setup(FileSetup.CUSTOMER.value)
        driver_setup = utils.read_setup(FileSetup.DRIVER.value)
        net_setup = utils.read_setup(FileSetup.NET.value)
        simulator_setup = utils.read_setup(FileSetup.SIMULATOR.value)
        uber_setup = utils.read_setup(FileSetup.UBER.value)
        self.uber = Uber(uber_setup["fare"],uber_setup["request"])
        self.net = Net(net_setup["info"], net_setup["areas"])
        self.driver_move_policy = driver_setup["move_policy"]
        self.customer_personality_policy = customer_setup["personality_policy"]
        self.driver_personality_policy = driver_setup["personality_policy"] 
        self.driver_id_counter = 0
        self.customer_id_counter = 0
        self.timer_remove_driver_idle = simulator_setup["timer_remove_driver_idle"]
        self.type = simulator_setup["type"].upper()
        self.checkpoints = simulator_setup["checkpoints"]
        self.scenario = dispatch_scenario.dispatch(self.type)

        if (self.type == SimulationType.PEAK.value):
            self.peak_simulation = simulator_setup["peak_simulation"]
        elif (self.type == SimulationType.GREEDY.value):
            self.fault_simulation_step = simulator_setup["fault_simulation_setup"]
        elif (self.type != SimulationType.NORMAL.value):
            print(self.type)
            print(SimulationType.NORMAL)
            raise Exception("Simulation type not found!")


    # Initialize edges speed
    def __init_net_edges_speed(self):
        edge_prefix = self.net.edge_prefix
        for i in range(self.net.min_edge_num, self.net.max_edge_num + 1):
            # random speed betweeen 9 and 21 m/s
            speed = random.randrange(9, 21)
            # set edge speed in both directions
            self.traci.edge.setMaxSpeed(f"{edge_prefix}{i}", speed)
            self.traci.edge.setMaxSpeed(
                f"-{edge_prefix}{i}", random.randrange(9, 21))


    # Generate random routes
    def __init_random_routes(self, route_prefix, min_edge_num, max_edge_num, num_routes, factor=5):
        for i in range(num_routes):
            # set route id
            route_id = f"{route_prefix}_route_{i}"
            # set route endpoints
            from_edge = random.randrange(min_edge_num, max_edge_num + 1)
            to_edge = random.randrange(min_edge_num, max_edge_num + 1)
            prefix_from = "" if utils.random_choice(0.5) else "-"
            prefix_to = "" if utils.random_choice(0.5) else "-"
            # check the endpoints have a distance greater than the factor (es. factor = 5 means the distance between the starting edge
            # and the ending edge is of at least 5 edges)
            while(abs(to_edge - from_edge) < factor):
                to_edge = random.randrange(min_edge_num, max_edge_num)
            # generate fastest route
            edge_prefix = self.net.edge_prefix
            route_stage = self.traci.simulation.findRoute(f"{prefix_from}{edge_prefix}{from_edge}", f"{prefix_to}{edge_prefix}{to_edge}")
            # add route
            self.traci.route.add(route_id, route_stage.edges)


    # Create customer
    def create_customer(self, timestamp, area_id):
        # print("create_customer")
        edges = self.net.areas[area_id].edges
        customer_personality_distribution = self.net.areas[area_id].customer_personality_distribution
        # create new customer instance
        new_customer = Customer(timestamp, self.customer_id_counter, area_id, edges, self.net.edge_prefix, customer_personality_distribution)
        # set customer position
        new_customer.pos = random.randrange(int(self.traci.lane.getLength(f'{new_customer.from_edge}_0')))
        # add customer in the scene
        self.traci.person.add(new_customer.id, new_customer.from_edge, new_customer.pos, depart=timestamp)
        # update id generator counter
        self.customer_id_counter += 1
        # append customer to corresponding area and update counter
        self.net.areas[area_id].customers.append(new_customer.id)
        # WARNING: the current version generate a request immediately
        self.create_customer_request(timestamp, new_customer)

    # Create customer request
    def create_customer_request(self, timestamp, customer):
        # create customer request
        self.traci.person.appendDrivingStage(customer.id, customer.to_edge, 'taxi')
        # append request to uber pending request list
        reservation = self.traci.person.getTaxiReservations(1)
        # catch traci unexpected behavior
        if not (len(reservation) == 1):
            print("Unexpected number of reservations in create_customer_request")
        # create ride request
        ride_request = Ride(timestamp, reservation[0])
        # send request to Uber
        self.uber.receive_request(ride_request, customer.id)


    # Create driver - add vehicle to the network. Simulate a driver that becomes active
    def create_driver(self, timestamp, area_id):
        # print("create_driver")
        driver_personality_distribution = self.net.areas[area_id].driver_personality_distribution

        # create new driver instance
        new_driver = Driver(timestamp, self.driver_id_counter, area_id, self.net.num_random_routes, driver_personality_distribution)
        # add driver to the scene
        self.traci.vehicle.add(new_driver.id, new_driver.route_id, "driver", depart=f'{timestamp}', departPos="random", line="taxi")
        # set driver current edge position
        new_driver.current_edge = self.traci.vehicle.getRoute(new_driver.id)[-1]
        # update driver list and id generator counter
        self.uber.idle_drivers.append(new_driver)
        self.uber.drivers[new_driver.id] = new_driver
        self.driver_id_counter += 1
        # append driver to corresponding area and update counter
        self.net.areas[area_id].drivers.append(new_driver.id)

    # Dispatch pending rides
    def dispatch_rides(self, timestamp):
        unprocessed_requests = self.uber.unprocessed_requests
        for ride in unprocessed_requests:
            customer_id = ride.customer_id
            for customer in self.customers:
                if(customer.id == customer_id):
                    area = self.net.areas[customer.area_id]
                    if (customer.accept_ride_choice(area, self.customer_personality_policy)):
                        driver_distances = []
                        for driver in self.uber.idle_drivers:
                            # compute waiting time
                            driver_edge = self.traci.vehicle.getRoadID(driver.id)
                            customer_edge = self.traci.person.getRoadID(customer.id)

                            if (self.net.is_valid_edge(driver_edge) and self.net.is_valid_edge(customer_edge)):
                                try:
                                    waiting_route_stage = self.traci.simulation.findRoute(driver_edge, customer_edge)
                                    expected_waiting_time = waiting_route_stage.travelTime
                                    waiting_distance = waiting_route_stage.length
                                    driver_distances.append({
                                        "driver_id": driver.id,
                                        "expected_waiting_time": expected_waiting_time,
                                        "waiting_distance": waiting_distance
                                    })
                                except:
                                    print("Unexpected Route not found in dispatch_rides")
                        
                        ride_route_stage = self.traci.simulation.findRoute(ride.from_edge, ride.to_edge)
                        ride_travel_time = ride_route_stage.travelTime
                        ride_length = ride_route_stage.length

                        ride.update_pending_request(ride_length, ride_travel_time)
                        self.uber.update_pending_request(ride)

                        from_edge_area_id = self.net.edge_area(ride.from_edge)

                        if (len(driver_distances) > 0):
                            drivers_sorted = sorted(driver_distances, key=lambda x:x["expected_waiting_time"], reverse=False)

                            # simulate send request to drivers
                            for driver_ride_request in drivers_sorted:
                                if (driver_ride_request["waiting_distance"] > self.uber.request_max_driver_distance):
                                    break
                                
                                driver_accept_ride = False
                                for driver in self.uber.idle_drivers:
                                    if (driver.state == DriverState.MOVING.value):
                                        to_area = self.net.edge_area(driver.current_edge)
                                        if (to_area != from_edge_area_id):
                                            continue

                                    if (driver.id == driver_ride_request['driver_id']):
                                        driver_accept_ride = driver.accept_ride_choice(area,self.driver_personality_policy)
                                        if (driver_accept_ride):
                                            expected_price = self.uber.compute_price(ride_travel_time,ride_length, area.surge_multiplier)
                                            ride.update_pickup(timestamp, driver, driver_ride_request, expected_price, area.surge_multiplier)
                                            driver.state = DriverState.PICKUP.value
                                            driver.ride_stats = {
                                                "ride_id": ride.id,
                                                "ride_request": timestamp,
                                                "customer_id": customer.id,
                                            }
                                            driver.update_pickup_ride()
                                            self.uber.update_pickup_ride(timestamp, ride, driver, customer)
                                            self.traci.vehicle.dispatchTaxi(driver.id, [ride.id])
                                    break
                                
                                if not (driver_accept_ride):
                                    ride.rejections += 1 
                        
                        if not (self.ride.state == RideState.PICKUP.value):
                            # WARNING: the current version cancel the ride anyway
                            cancel_ride = utils.random_choice(1)
                            if (cancel_ride) :
                                self.traci.person.removeStages(customer_id)
                                ride.update_cancel(timestamp)
                                area.update_cancel_ride(customer.id)
                                self.uber.update_cancel_ride(ride)
                                self.traci.person.removeStages(customer.id)
                            else:
                                print("Error: why here?")
                                pass
                    else:
                        self.traci.person.removeStages(customer.id)


    def expected_travel_time(self, edges):
        #print("expected_travel_time")
        travel_time = 0
        for edge_id in edges:
            travel_time += self.traci.edge.getTraveltime(edge_id)
        return travel_time


    def init_scenario(self):
        self.__init_net_edges_speed()
        num_random_routes = self.net.num_random_routes
        for area_id, area_data in self.net.areas.items():
            min_edge_num = area_data.edges[0]
            max_edge_num = area_data.edges[1]

            print(f"GENERATE ROUTES WITHIN AREA {area_id}")
            self.__init_random_routes(f"area_{area_id}", min_edge_num, max_edge_num, num_random_routes)

            print(f"GENERATE RANDOM DRIVERS WITHIN AREA {area_id}")
            for i in range(10):
                if (utils.random_choice(area_data.generation_policy["driver"])):
                    self.create_driver(0, area_id)

            print(f"GENERATE RANDOM CUSTOMERS WITHIN AREA {area_id}")
            for i in range(10):
                if (utils.random_choice(area_data.generation_policy["customer"])):
                    self.create_customer(0, area_id)

        print(f"GENERATE ROUTES INTER-AREAS")
        min_edge_num = self.net.min_edge_num
        max_edge_num = self.net.max_edge_num
        self.__init_random_routes(f"inter_areas", min_edge_num, max_edge_num, num_random_routes*5, factor=150)


    # Move driver to area
    def move_driver_to_area(self, driver, area_id):
        # print("move_driver_to_different_area")
        edges = net.areas[area_id]["edges"]
        from_edge, to_edge = driver.generate_from_to(self.net.edge_prefix, edges)
        if not (from_edge == "") and not (("gneJ" in from_edge) or ("-gneJ" in from_edge)):
            try:
                route_stage = self.simulation.findRoute(from_edge, to_edge)
                self.traci.vehicle.setRoute(driver.id, route_stage.edges)
                driver.route_id = "moving_route"
            except:
                pass

    
    # Remove driver
    def remove_driver(self, timestamp, driver):
        # print("remove_driver")
        driver.remove(timestamp)
        self.uber.update_remove_driver(driver)
        for area_id, area in self.net.areas.items():
            if (driver.id in area.drivers):
                area.remove_driver(driver.id)
                break
        try:
            # remove vehicle from the scene
            self.traci.vehicle.remove(driver.id)
        except:
            print("Unexpected driver not found in remove_driver")
            print(driver)
            pass


    def run(self):
        print('RUN')
        step = 0
        stop = False

        while not stop:
            self.traci.simulationStep()
            timestamp = self.traci.simulation.getTime()
            step += 1

            if (step % time_update_surge == 0):
                self.update_surge_multiplier()

            self.update_drivers(timestamp)
            self.update_drivers_area()
            self.update_rides_state(timestamp, step)

            if (step % self.checkpoints["time_driver_generation"]) == 0:
                for area_id, area in self.net.areas.items():
                    for i in range(area.generation["many"][1]):
                        if (utils.random_choice(area.generation["driver"])):
                            self.create_driver(timestamp, area_id)

            if (step % self.checkpoints["time_customer_generation"]) == 0:
                for area_id, area in self.net.areas.items():
                    for i in range(area.generation["many"][0]):
                        if (utils.random_choice(area.generation["customer"])):
                            self.create_customer(timestamp, area_id)

            if (step % self.checkpoints["time_dispatch_rides"]) == 0:
                self.dispatch_rides(timestamp)

            if (step % self.checkpoints["time_move_driver"]) == 0:
                self.update_drivers_movements()

            self.scenario.thrown_scenario(step, self.net)


            if (step == self.checkpoints["simulation_duration"]):
                self.printer.save_ride_stats(ride)
                self.printer.save_global_stats(step)
                stop = True

        self.traci.close()
        sys.stdout.flush()


    def update_drivers(self, timestamp):
        #print("update_drivers")
        for driver in self.uber.drivers:
            surge_multiplier = self.net.areas[driver.area_id].surge_multiplier
            idle_timer_over = (timestamp - driver.last_ride) > self.timer_remove_driver_idle
            traci_remove = driver.id in list(self.traci.simulation.getArrivedIDList())
            if (driver.state == DriverState.IDLE.value and (idle_timer_over or traci_remove)):
                #print(driver)
                self.remove_driver(timestamp, driver)


    def update_drivers_area(self):
        #print("update_drivers_area")
        for driver_id, driver in self.uber.drivers.items():
            if not (driver.state == DriverState.INACTIVE.value):
                try:
                    current_edge = self.traci.vehicle.getRoadID(driver.id)
                    if (self.net.is_valid_edge(current_edge)):
                        driver.current_edge = current_edge

                    area_id = self.net.edge_area(driver.current_edge)

                    if not ((area_id == "") or (driver["area_id"] == area_id)):
                        self.net.areas[driver.area_id].drivers.remove(driver.id)
                        self.net.areas[area_id].drivers.append(driver.id)
                        driver.area_id = area_id

                        if (driver.state == DriverState.MOVING.value):
                            to_area = self.traci.vehicle.getRoute(driver.id)[-1]
                            
                            if not (to_area == "" and to_area == driver.id):
                                driver.state = DriverState.IDLE.value
                except:
                    print(f"Unexpected driver not found in update_drivers_area\n")
                    print(driver)
                    continue

    
    def update_drivers_movements(self):
        #print("update_drivers_movements")
        for area_id, area in self.net.areas.items():
            move_probability = 0
            for other_area_id, other_area in self.net.areas.items(): 
                if not (other_area_id == area_id):
                    for min_diff, max_diff, p in self.driver_move_policy["move_diff_probabilities"]:
                        if (((area.surge_multiplier - other_area.surge_multiplier) > min_diff) and ((area.surge_multiplier - other_area.surge_multiplier) <= max_diff)):
                            move_probability = p
                            break

                    for driver_id in other_area.drivers:
                        driver = self.uber.drivers[driver_id]
                        if (driver.state == DriverState.IDLE.value):
                            if (utils.random_choice(move_probability)):
                                print(f"Move driver {driver_id} from area {other_area_id} to area {area_id}")
                                self.move_driver_to_area(driver,area_id)


    def update_rides_state(self, timestamp, step):
        #print("update_rides_state")
        traci_idle_drivers = self.traci.vehicle.getTaxiFleet(0)

        for ride in self.uber.onroad_rides:
            driver = self.uber.drivers[ride.driver_id]
            customer = self.uber.customers[ride.customer_id]

            if (ride.driver_id in traci_idle_drivers):
                # update area
                from_edge_area_id = self.net.edge_area(ride.from_edge)
                from_area = self.net.areas[from_edge_area_id]
                from_area.update_end_ride(ride)

                # update driver
                to_edge_area_id = self.net.edge_area(ride.to_edge)
                to_area = self.net.areas[to_edge_area_id]
                driver = self.uber.drivers[ride.driver_id]
                driver.update_end_ride(timestamp, to_edge_area_id, self.net.num_random_routes)

                if (timestamp - driver.start > 3600):
                    stop_drive = utils.random_choice(0.6)
                    if (stop_drive or to_area.surge_multiplier <= 0.6):
                        self.remove_driver(timestamp, driver)

                # update ride stats
                ride.update_end(timestamp, step)
                ride.stats["price"] = self.uber.compute_price(ride.stats["ride_time"], ride.stats["ride_length"], from_area.surge_multiplier)

                # update uber
                self.uber.update_end_ride(ride)

                # save statistics
                self.printer.save_ride_stats(ride)
                self.printer.save_global_stats(step)

        for ride in self.uber.pickup_rides:
            driver = self.uber.drivers[ride.driver_id]
            customer = self.uber.customers[ride.customer_id]
            if driver.current_edge == customer.current_edge:
                ride.update_onroad(timestamp)
                self.uber.update_onroad_ride(ride)


    def update_surge_multiplier(self):
        #print("update_surge_multiplier")
        for area_id, area in self.net.areas.items():
            idle_drivers_in_area = 0
            for driver in self.uber.idle_drivers:
                if (driver.state == DriverState.MOVING.value):
                    to_area = self.net.edge_area(driver.current_edge)
                    if (to_area == area_id):
                        idle_drivers_in_area += 1
                elif (driver.area_id == area_id and driver.state == DriverState.IDLE.value):
                    idle_drivers_in_area += 1

            balance = 0
            idle_customers = 0

            for customer_id in area.customers:
                if not (customer_id in self.uber.customers):
                    idle_customers += 1
                elif (customer_id in self.uber.rides):
                    ride = self.uber.rides[customer_id]
                    if (ride.state in [RideState.PENDING.value, RideState.REQUESTED.value]):
                        idle_customers += 1

            if (idle_customers > 0):
                if (idle_drivers_in_area == 0):
                    balance = 1/(idle_customers + 0.1)
                else:
                    balance = (idle_drivers_in_area)/(idle_customers)
            else:
                balance = idle_drivers_in_area

            area.stats["balances"].append(balance)
            surge_multiplier = area.surge_multiplier

            for min_balance, max_balance, value in self.uber.surge_multiplier_policy:
                if (balance >= min_balance and balance < max_balance):
                    surge_multiplier += value
                    break
            
            area.surge_multiplier = max(0.7,min(surge_multiplier,3.5))
            area.stats["surge_multipliers"].append(max(0.7,min(surge_multiplier,3.5)))


    def __str__(self):
        simulator_str = "*"*10
        simulator_str += "\nSIMULATION\n"
        simulator_str += "*"*10
        simulator_str += '\n\n'
        simulator_str = "-"*9
        simulator_str += "\nSIMULATOR\n"
        simulator_str += "-"*9
        simulator_str += '\n\n'
        simulator_str += f"type: {self.type}\n"
        simulator_str += f"duration: {self.checkpoints['simulation_duration']}\n"
        
        simulator_str += f"checkpoints: \n"
        for key, value in self.checkpoints.items():
            key_str = key.replace("_"," ")
            simulator_str += f"     - {key_str}: {value}\n"

        simulator_str += f"driver mobility policies: \n"
        for key, value_list in self.driver_move_policy.items():
            key_str = key.replace("_"," ")
            simulator_str += f"     - {key_str}:\n"
            for min_surge, max_surge, probability in value_list:
                simulator_str += f"        - [{min_surge},{max_surge}] --> {probability}\n"

        simulator_str += f"driver personality policy: \n"
        for key, value_list in self.driver_personality_policy.items():
            key_str = key.replace("_"," ")
            simulator_str += f"     - {key_str}:\n"
            for min_surge, max_surge, probability in value_list:
                simulator_str += f"        - [{min_surge},{max_surge}] --> {probability}\n"

        simulator_str += f"timer remove idle driver: {self.timer_remove_driver_idle}\n"
        
        simulator_str += f"customer personality policy: \n"
        for key, value_list in self.customer_personality_policy.items():
            key_str = key.replace("_"," ")
            simulator_str += f"     - {key_str}:\n"
            for min_surge, max_surge, probability in value_list:
                simulator_str += f"        - [{min_surge},{max_surge}] --> {probability}\n"

        simulator_str += "\n"
        simulator_str += str(self.uber)
        simulator_str += "\n"
        simulator_str += str(self.net)
        simulator_str += "\n"
        simulator_str += "*"*10
        return simulator_str
        
