# @file    runner.py
# @author  Davide
# @date    2021-04-30


from __future__ import absolute_import
from __future__ import print_function
from copy import copy
from pathlib import Path
import random
import math
import os
import sys
import optparse
import csv


# we need to import python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
import sumolib

from classes.Simulator import Simulator

from init import *

# Create driver - add vehicle in the network. Simulate a driver that becomes active
def create_driver(timestamp,area_id):
    #print("create_driver")
    global driver_id_counter
    driver_id = f"driver_{driver_id_counter}"
    num_random_routes = net_info["num_random_routes"]
    route_num = random.randrange(0,num_random_routes)
    route_id = f"area_{area_id}_route_{route_num}"
    traci.vehicle.add(driver_id, route_id, "driver", depart=f'{timestamp}', departPos="random", line="taxi")
    areas[area_id]["drivers"].append(driver_id)
    areas[area_id]["drivers_counter"] += 1
    driver_id_counter += 1

    drivers_list.append({
        "driver_id": driver_id,
        "area_id": area_id,
        "state": "active",
        "start": timestamp,
        "last_ride": timestamp,
        "personality": assign_personality(areas[area_id]["driver_personality_probability_distribution"])
    })

def move_driver_to_different_area(driver_id,area_id):
    #print("move_driver_to_different_area")
    min_edge = areas[area_id]["edges"][0]
    max_edge = areas[area_id]["edges"][1]
    from_edge = traci.vehicle.getRoadID(driver_id)
    prefix_to = "" if random_choice(0.5) else "-"
    edge_prefix = net_info["edge_prefix"]
    to_edge = f"{prefix_to}{edge_prefix}{random.randrange(min_edge,max_edge + 1)}"

    if not (from_edge == "") and not (("gneJ" in from_edge) or ("-gneJ" in from_edge)):
        try:
            route_stage = traci.simulation.findRoute(from_edge,to_edge)
            traci.vehicle.setRoute(driver_id,route_stage.edges)
        except:
            pass

def remove_driver(driver_id):
    #print("remove_driver")
    for driver in drivers_list:
        if (driver["driver_id"] == driver_id):
            driver["state"] = "inactive"
    for area_id, area_data in areas.items():
        if (driver_id in area_data["drivers"]):
            area_data["drivers"].remove(driver_id)
            areas[area_id]["drivers_counter"] -= 1
    try:
        traci.vehicle.remove(driver_id)
    except:
        pass

# Creating customer
def create_customer(timestamp,area_id):
    #print("create_customer")
    global customer_id_counter
    customer_id = f"customer_{customer_id_counter}"
    min_edge = areas[area_id]["edges"][0]
    max_edge = areas[area_id]["edges"][1]
    from_edge = random.randrange(min_edge,max_edge+1)
    to_edge = random.randrange(min_edge,max_edge+1)

    while from_edge == to_edge:
        to_edge = random.randrange(min_edge,max_edge+1)

    prefix_from = "" if random_choice(0.5) else "-"
    prefix_to = "" if random_choice(0.5) else "-"
    pos = random.randrange(int(traci.lane.getLength(f'gneE{from_edge}_0')))
    traci.person.add(customer_id, f'{prefix_from}gneE{from_edge}', pos, depart=timestamp)
    traci.person.appendDrivingStage(customer_id,f'{prefix_to}gneE{to_edge}','taxi')
    customer_id_counter += 1
    areas[area_id]["customers"].append(customer_id)
    areas[area_id]["customers_counter"] += 1

    customers_list.append({
        "customer_id": customer_id,
        "personality": assign_personality(areas[area_id]["customer_personality_probability_distribution"]),
        "area_id": area_id
    })


def assign_personality(distribution):
    value = random.random()
    for threshold, personality in distribution:
        if (value <= threshold):
            return personality
    return "normal"


# Dispatch pending rides
def dispatch_rides(timestamp):
    #print("dispatch_ride")
    #pending rides
    #for request in traci.person.getTaxiReservations(1):
    #    pending_rides.append({
    #        "id": request.id,
    #        "customer_id": request.persons[0],
    #        "reservation": request,
    #        "status": "new"
    #    })
    pending_rides.extend(list(traci.person.getTaxiReservations(1)))

    # filter idle drivers
    idle_drivers = list(traci.vehicle.getTaxiFleet(0))

    for ride in pending_rides:
        if (not ride.id in rides_stats):
            # retrieve first customer of the current ride
            customer_id = ride.persons[0]

            for customer in customers_list:
                if(customer["customer_id"] == customer_id):
                    if (accept_ride_choice(customer["area_id"],"customer", customer["personality"])):
                        # customer coordinates
                        x_c,y_c = traci.person.getPosition(customer_id)

                        driver_distances = []
                        for driver_id in idle_drivers:
                            # driver coordinates
                            x_d,y_d = traci.vehicle.getPosition(driver_id)
                            # compute distance of the driver from the customer
                            #air_distance = abs(traci.simulation.getDistance2D(x_c,y_c,x_d,y_d,isDriving=False))
                            #road_distance = abs(traci.simulation.getDistance2D(x_c,y_c,x_d,y_d,isDriving=True))

                            # compute waiting time
                            driver_edge = traci.vehicle.getRoadID(driver_id)
                            customer_edge = traci.person.getRoadID(customer_id)

                            if not (driver_edge == "") and not (("gneJ" in driver_edge) or ("-gneJ" in driver_edge)):
                                if not (customer_edge == "") and not (("gneJ" in customer_edge) or ("-gneJ" in customer_edge)):
                                    try:
                                        waiting_route_stage = traci.simulation.findRoute(driver_edge,customer_edge)
                                        expected_waiting_time = waiting_route_stage.travelTime
                                        waiting_distance = waiting_route_stage.length

                                        driver_distances.append({
                                            "driver_id": driver_id,
                                            #"road_distance": road_distance,
                                            #"air_distance": air_distance,
                                            "expected_waiting_time": expected_waiting_time,
                                            "waiting_distance": waiting_distance
                                        })
                                    except:
                                        pass

                        ride_route_stage = traci.simulation.findRoute(ride.fromEdge, ride.toEdge)
                        ride_travel_time = ride_route_stage.travelTime
                        ride_length = ride_route_stage.length

                        ride_stats = rides_stats[ride.id] if ride.id in rides_stats else {
                            "id": ride.id,
                            "customer_id": customer_id,
                            "found": False,
                            "canceled": False,
                            "expected_ride_length": ride_length,
                            "expected_ride_time": ride_travel_time,
                            "rejections": 0,
                            "steps": 0,
                            "timestamp_request": timestamp,
                            "state": "pending",
                            "from": ride.fromEdge,
                            "to": ride.toEdge,
                            "reservation": ride
                        }

                        from_edge_area_id = edge_area(ride.fromEdge)

                        if (len(driver_distances) > 0):
                            drivers_sorted = sorted(driver_distances, key=lambda x:x["expected_waiting_time"], reverse=False)

                            # simulate send request to drivers
                            for driver_ride_data in drivers_sorted:
                                if (driver_ride_data["waiting_distance"] > request_driver_distance):
                                    break
                                
                                driver_accept_ride = False

                                for d in drivers_list:
                                    if (d["state"] == "moving"):
                                        to_area = edge_area(traci.vehicle.getRoute(d["driver_id"])[-1])
                                        if (to_area != from_edge_area_id):
                                            continue

                                    if (d["driver_id"] == driver_ride_data['driver_id']):
                                        driver_accept_ride = accept_ride_choice(from_edge_area_id,"driver",d["personality"])
                                        if (driver_accept_ride):
                                            d["state"] = "occupied"
                                            d["ride_id"] = ride.id
                                            d["customer_id"] = customer_id
                                        break
                                            
                                if (driver_accept_ride):
                                    #print("IDLE DRIVERS")
                                    #print(idle_drivers)
                                    idle_drivers.remove(driver_ride_data["driver_id"])
                                    #print(idle_drivers)
                                    pending_rides.remove(ride)
                                    onroad_rides.append(ride)
                                    ride_stats["found"] = True
                                    ride_stats["driver_id"] = driver_ride_data["driver_id"]
                                    ride_stats["expected_waiting_length"] = driver_ride_data["waiting_distance"]
                                    ride_stats["expected_total_length"] = ride_length + driver_ride_data["waiting_distance"]
                                    ride_stats["expected_waiting_time"] = driver_ride_data["expected_waiting_time"]
                                    ride_stats["expected_total_time"] = driver_ride_data["expected_waiting_time"] + ride_travel_time
                                    ride_stats["expected_price"] = compute_price(ride_travel_time,ride_length, areas[from_edge_area_id]["surge_multipliers"][-1])
                                    ride_stats["timestamp_accepted"] = timestamp
                                    ride_stats["surge_multiplier"] = areas[from_edge_area_id]["surge_multipliers"][-1]
                                    ride_stats["time_to_accept_request"] = timestamp - ride_stats["timestamp_request"]
                                    ride_stats["state"] = "waiting"
                                    rides_stats[ride.id] = ride_stats
                                    
                                    #print('***')
                                    #print(f"Driver {driver_ride_data['driver_id']} route before: {traci.vehicle.getRoute(driver_ride_data['driver_id'])}")
                                    #print(f"Customer {customer_id} road: {traci.person.getRoadID(customer_id)}") 
                                    traci.vehicle.dispatchTaxi(driver_ride_data["driver_id"], [ride.id])
                                    #print(f"Driver {driver_ride_data['driver_id']} route after: {traci.vehicle.getRoute(driver_ride_data['driver_id'])}")
                                    #print("***")
                                    matched_rides.append((customer_id,driver_ride_data['driver_id'],timestamp))

                                    areas[from_edge_area_id]["customers_counter"] -= 1
                                    break
                                else:
                                    ride_stats["rejections"] = ride_stats["rejections"] + 1 

                        if not (ride_stats["found"]):
                            cancel_ride = random_choice(cancel_ride_p)
                            if (cancel_ride) :
                                #print(f"customer: {customer_id} - driver not found")
                                traci.person.removeStages(customer_id)
                                ride_stats["canceled"] = True
                                ride_stats["state"] = "canceled"
                                areas[from_edge_area_id]["canceled"] += 1
                                pending_rides.remove(ride)
                                areas[from_edge_area_id]["customers_counter"] -= 1
                                areas[from_edge_area_id]["customers"].remove(customer_id)
                                canceled_rides.append(customer_id)
                                customers_list.remove(customer)
                                #areas[from_edge_area_id]["surge_multipliers"].append(areas[from_edge_area_id]["surge_multipliers"][-1] + 0.1)
                            else:
                                #print(f"customer: {customer_id} - driver not found")
                                #ride_stats["steps"] += 1
                                #rides_stats[ride.id] = ride_stats
                                traci.person.removeStages(customer_id)
                                areas[from_edge_area_id]["customers_counter"] -= 1
                                ride_stats["canceled"] = True
                                ride_stats["state"] = "canceled"
                                areas[from_edge_area_id]["canceled"] += 1
                                pending_rides.remove(ride)
                                canceled_rides.append(customer_id)
                                areas[from_edge_area_id]["customers"].remove(customer_id)
                                customers_list.remove(customer)
                                #areas[from_edge_area_id]["surge_multipliers"].append(areas[from_edge_area_id]["surge_multipliers"][-1] + 0.1)


                        # print statistics
                        #print_dispatch_ride_stats(ride_stats)
                    else:
                        traci.person.removeStages(customer_id)
                        areas[customer["area_id"]]["customers_counter"] -= 1
                        customers_list.remove(customer)


def edge_area(edge_id):
    #print("edge_area")
    for area_id, area_data in areas.items():
        edges_names = []
        for i in range(area_data["edges"][0],area_data["edges"][1]+1):
            edges_names.append(f"gneE{i}")
            edges_names.append(f"-gneE{i}")
        if (edge_id in edges_names):
            return area_id
    return ""

# return a random choice with a certain probability
def random_choice(p=0.5):
    #print("random_choice")
    return random.random() < p

def expected_travel_time(edges):
    #print("expected_travel_time")
    travel_time = 0
    for edge_id in edges:
        travel_time += traci.edge.getTraveltime(edge_id)
    return travel_time

# computed expected price of the ride
def compute_price(travel_time, ride_length, surge_price_multiplier):
    #print("compute_price")
    price = (base_fare + (fee_per_minute * travel_time) + (fee_per_mile * ride_length/1000)) * surge_price_multiplier
    return price


def accept_ride_choice(area_id, agent, personality):
    surge_multiplier = areas[area_id]["surge_multipliers"][-1]
    policies = personality_driver_policy if agent == "driver" else personality_customer_policy
    choice_policy = policies[personality]

    for min_surge, max_surge, p in choice_policy:
        if (surge_multiplier >= min_surge and surge_multiplier < max_surge):
            return random_choice(p)

    return random_choice(0.5)




def update_surge_multiplier():
    #print("update_surge_multiplier")
    idle_drivers = traci.vehicle.getTaxiFleet(0)

    #print(f"IDLE DRIVERS: {idle_drivers}")

    for area_id, area_data in areas.items():
        customers_in_area = areas[area_id]["customers_counter"]
        #drivers_in_area = areas[area_id]["drivers_counter"]
        #idle_drivers_in_area = len(list(set(idle_drivers).intersection(areas[area_id]["drivers"])))
        idle_drivers_in_area = 0
        
        for driver in drivers_list:
            if (driver["state"] == "moving"):
                to_area = edge_area(traci.vehicle.getRoute(driver["driver_id"]))
                if (to_area == area_id):
                    idle_drivers_in_area += 1

            elif (driver["area_id"] == area_id and driver["state"] == "active"):
                idle_drivers_in_area += 1

        
        #print(f"IDLE DRIVERS IN AREA {area_id}: {idle_drivers_in_area}")
        #print(f"CUSTOMERS IN AREA {area_id}: {customers_in_area}")

        if (customers_in_area > 0):
            #balance = (idle_drivers_in_area)/(customers_in_area)
            #print(f"balance: {balance}")
            if (idle_drivers_in_area == 0):
                balance = 1/(customers_in_area + 0.1)
            else:
                balance = (idle_drivers_in_area)/(customers_in_area)
        else:
            balance = idle_drivers_in_area

        print(f"customers_in_area: {customers_in_area}")
        print(f"drivers_in_area: {idle_drivers_in_area}")

        diff_balance = balance - area_data["balances"][-1]
        area_data["balances"].append(balance)
        surge_multiplier = area_data["surge_multipliers"][-1]

        for min_balance, max_balance, value in surge_multiplier_policy:
            if (balance >= min_balance and balance < max_balance):
                #print(f"Before: {surge_multiplier}")
                print(f"Add: {value}")
                surge_multiplier += value
                break

        #for min_diff, max_diff, value in surge_multiplier_policy:
        #    if (abs(diff_balance) >= min_diff and abs(diff_balance) < max_diff):
        #        if (diff_balance > 0):
        #            surge_multiplier -= value
        #        else:
        #            if(surge_multiplier > 0):
        #                surge_multiplier += value
        #        break
        
        area_data["surge_multipliers"].append(max(0.7,min(surge_multiplier,3.5)))

        print(f"Surge: {area_data['surge_multipliers'][-1]}")

        #print(f"Before: {area_data['surge_multiplier']}")
        #print(f"Surge = {surge_multiplier}")
        #print(f"Min: {min(surge_multiplier,3.5)}")
        #print(f"After: {area_data['surge_multiplier']}")

        if(area_data["surge_multipliers"][-1] > 3.5):
            print("ERROR!!!")
    print("-"*10)


def update_drivers_area():
    #print("update_drivers_area")
    for driver in drivers_list:
        if not (driver["state"] == "inactive"):
            driver_id = driver["driver_id"]
            #print(8)
            #print(removed_drivers)
            #print(drivers_list)

            try:
                traci.vehicle.getRoadID(driver_id)
            except:
                continue
                pass

            driver_edge = traci.vehicle.getRoadID(driver_id)
            #print(driver_edge)
            area_id = edge_area(driver_edge)

            if not ((area_id == "") or (driver["area_id"] == area_id)):
                areas[driver["area_id"]]["drivers"].remove(driver_id)
                areas[area_id]["drivers"].append(driver_id)
                driver["area_id"] = area_id

                if (driver["state"] == "moving"):
                    to_area = traci.vehicle.getRoute(driver_id)[-1]
                    
                    if not (to_area == "" and to_area == driver["area_id"]):
                        driver["state"] == "active"


def update_rides_state(timestamp,step):
    #print("update_rides_state")
    idle_drivers = traci.vehicle.getTaxiFleet(0)
    pickup_drivers = traci.vehicle.getTaxiFleet(1)
    occupied_drivers = traci.vehicle.getTaxiFleet(2)

    for ride_id, ride in rides_stats.items():
        if not (ride["canceled"]):
            driver_id = ride["driver_id"]
            customer_id = ride["customer_id"]

            if ride["state"] == "waiting":
                driver_edge = traci.vehicle.getRoadID(driver_id)
                customer_edge = traci.person.getRoadID(customer_id)
                if driver_edge == customer_edge:
                    ride["timestamp_pickup"] = timestamp
                    ride["waiting_time"] = timestamp - ride["timestamp_accepted"]
                    ride["state"] = "pickup"
            elif ((ride["state"] == "pickup") and  (driver_id in idle_drivers)):
                for driver in drivers_list:
                    if (driver["driver_id"] == ride["driver_id"]):
                        if (driver["state"] == "occupied"):
                            from_edge_area_id = edge_area(ride["from"])

                            ride["end_step"] = step
                            ride["timestamp_end"] = timestamp
                            ride["ride_time"] = timestamp - ride["timestamp_pickup"]
                            ride["ride_length"] = ride["expected_ride_length"]
                            ride["waiting_length"] = ride["expected_waiting_length"]
                            ride["total_time"] = timestamp - ride["timestamp_request"]
                            ride["total_length"] = ride["waiting_length"] + ride["ride_length"]
                            ride["price"] = compute_price(ride["ride_time"],ride["ride_length"],areas[from_edge_area_id]["surge_multipliers"][-1])
                            ride["state"] = "end"

                            areas[from_edge_area_id]["customers"].remove(ride["customer_id"])
                            areas[from_edge_area_id]["completed"] +=1
                            areas[from_edge_area_id]["waiting_times"].append(ride["waiting_time"])
                            areas[from_edge_area_id]["ride_times"].append(ride["ride_time"])
                            areas[from_edge_area_id]["total_times"].append(ride["total_time"])
                            areas[from_edge_area_id]["waiting_lengths"].append(ride["waiting_length"])
                            areas[from_edge_area_id]["ride_lengths"].append(ride["ride_length"])
                            areas[from_edge_area_id]["total_lengths"].append(ride["total_time"])
                            areas[from_edge_area_id]["expected_prices"].append(ride["expected_price"])
                            areas[from_edge_area_id]["prices"].append(ride["price"])
                            areas[from_edge_area_id]["diff_prices"].append(ride["price"] - ride["expected_price"])
                            areas[from_edge_area_id]["diff_waiting_times"].append(ride["waiting_time"] - ride["expected_waiting_time"])
                            areas[from_edge_area_id]["diff_ride_times"].append(ride["ride_time"] - ride["expected_ride_time"])
                            areas[from_edge_area_id]["diff_total_times"].append(ride["total_time"] - ride["expected_total_time"])
                            areas[from_edge_area_id]["diff_waiting_lengths"].append(ride["waiting_length"] - ride["expected_waiting_length"])
                            areas[from_edge_area_id]["diff_ride_lengths"].append(ride["ride_length"] - ride["expected_ride_length"])
                            areas[from_edge_area_id]["diff_total_lengths"].append(ride["total_length"] - ride["expected_total_length"])
                            areas[from_edge_area_id]["rejections"].append(ride["rejections"])


                            onroad_rides.remove(ride["reservation"])
                            ended_rides.append(ride["reservation"])
                            save_ride_stats(ride)
                            save_global_statistics(step)
                            

                            driver["state"] = "active"
                            driver["last_ride"] = timestamp
                            driver["ride_id"] = None
                            driver["customer_id"] = None
                            if (timestamp - driver["start"] > 3600):
                                stop_drive = random_choice(0.6)
                                if (stop_drive or areas[from_edge_area_id]["surge_multipliers"][-1] <= 0.6):
                                    remove_driver(driver_id)
                                    removed_drivers.append((driver,timestamp))
                
                for customer in customers_list:
                    if (customer["customer_id"] == customer_id):
                        customers_list.remove(customer)


def update_drivers_movements(timestamp):
    #print("update_drivers_movements")
    for area_id, area_data in areas.items():
        move_probability = 0

        for other_area_id,other_area_data in areas.items(): 
            if not (other_area_id == area_id):
                for min_diff, max_diff, p in move_diff_probabilities:
                    if (((area_data["surge_multipliers"][-1] - other_area_data["surge_multipliers"][-1]) > min_diff) and ((area_data["surge_multipliers"][-1] - other_area_data["surge_multipliers"][-1]) <= max_diff)):
                        move_probability = p
                        break

                for driver_id in other_area_data["drivers"]:
                    for driver in drivers_list:
                        if (driver["driver_id"] == driver_id and driver["state"] == "active"):
                            if (random_choice(move_probability)):
                                print(f"Move driver {driver_id} from area {other_area_id} to area {area_id}")
                                move_driver_to_different_area(driver_id,area_id)

def update_drivers(timestamp):
    #print("update_drivers")
    for driver in drivers_list:
        surge_multiplier = areas[driver["area_id"]]["surge_multipliers"][-1]
        if (not((driver["state"] == "occupied") or (driver["state"] == "inactive") or (driver["state"] == "moving")) and (((timestamp - driver["last_ride"]) > timer_remove_driver_idle) or (driver["driver_id"] in list(traci.simulation.getArrivedIDList())))):
            #print(driver)
            remove_driver(driver["driver_id"])
            removed_drivers.append((driver,timestamp))


def print_dispatch_ride_stats(ride_stats):
    #print("print_dispatch_ride_stats")
    print(ride_stats)

def print_area_stats():
    #print("area_stats")
    print("*"*15)
    print("AREA STATISTICS")
    print("*"*15)

    for area_id, area_data in areas.items():
        print('-'*6)
        print(f"AREA {area_id}")
        print('-'*20)
        print("GENERATION PROBABILITY:")
        print('-'*20)
        print(f"Customer: {area_data['generation']['customer']}")
        print(f"Driver: {area_data['generation']['driver']}")
        print(f"Surge Multiplier: {area_data['surge_multiplier']}")
        print(f"ACTIVE USERS IN THE AREA")
        print(f"Customers: {area_data['customers']}")
        print(f"Drivers: {area_data['drivers']}")
        print(f"Canceled: {area_data['canceled']}")
        print(f"Customers counter: {area_data['customers_counter']}")
        print('-'*20)

    #print(f"Canceled rides: {canceled_rides}")
    #print(f"Pending rides: {pending_rides}")
    #print(f"On road rides: {onroad_rides}")
    #print(f"Ended rides: {ended_rides}")
    #print(f"Matched rides: {matched_rides}")
    #print(f"Removed drivers: {removed_drivers}")


    for m in matched_rides:
        c= m[0]
        d = m[1]
        #print(f"Customer {c} position: {traci.person.getRoadID(c)}")
        #print(f"Driver {d} Route: {traci.vehicle.getRoute(d)}")

def save_simulation_statistics():
    #print("save_simulation_statistics")

    with open(f"stats_file_{time_simulation}", 'a', newline='\n') as stats_writer:
        stats_writer.write("*"*21)
        stats_writer.write("\nSIMULATION PARAMETERS\n")
        stats_writer.write("*"*21)
        stats_writer.write('\n')
        stats_writer.write(f"Fault simulation: {'TRUE' if fault_simulation else 'FALSE'}\n")
        for min_surge, max_surge, p in move_probabilities:
            stats_writer.write(f"Move driver probability with surge multiplier between {min_surge} and {max_surge}: {p}\n")
        for min_diff, max_diff, value in surge_multiplier_policy:
            stats_writer.write(f"Surge multiplier policy with balance variations between {min_diff} and {max_diff}: {value}\n")
        
        stats_writer.write('\n')
        stats_writer.write("*"*30)
        stats_writer.write("\nPERSONALITY ACCEPT RIDE POLICY\n")
        stats_writer.write("*"*30)
        stats_writer.write("\nDriver Policy\n")
        stats_writer.write("-"*13)
        for personality, probabilities in personality_driver_policy.items():
            stats_writer.write(f"\nPersonality: {personality}\n")
            for min_p, max_p, accept_p in probabilities:
                stats_writer.write(f"Accept probability with surge multiplier between {min_p} and {max_p}: {accept_p}\n")
        stats_writer.write("-"*15)
        stats_writer.write("\nCustomer Policy\n")
        stats_writer.write("-"*15)
        for personality, probabilities in personality_customer_policy.items():
            stats_writer.write(f"\nPersonality: {personality}\n")
            for min_p, max_p, accept_p in probabilities:
                stats_writer.write(f"Accept probability with surge multiplier between {min_p} and {max_p}: {accept_p}\n")
        stats_writer.write("\n")

        stats_writer.write("*"*15)
        stats_writer.write("\nAREA STATISTICS\n")
        stats_writer.write("*"*15)

        for area_id, area_data in areas.items():
            stats_writer.write(f"\nAREA {area_id}\n")
            stats_writer.write('-'*22)
            stats_writer.write("\nGENERATION PROBABILITY\n")
            stats_writer.write('-'*22)
            stats_writer.write("\n")
            stats_writer.write(f"Customer: {area_data['generation']['customer']}\n")
            stats_writer.write(f"Driver: {area_data['generation']['driver']}\n")
            stats_writer.write('-'*9)
            stats_writer.write(f"\nSTATISTICS\n")
            stats_writer.write('-'*9)
            stats_writer.write('\n')
            stats_writer.write(f"Average Surge Multiplier: {average(area_data['surge_multipliers']):.2f}\n")
            stats_writer.write(f"Average Balance: {average(area_data['balances']):.2f} drivers/customer\n")
            stats_writer.write(f"Ride Canceled: {area_data['canceled']}\n")
            stats_writer.write(f"Rides completed: {area_data['completed']}\n")
            stats_writer.write(f"Average Rejections: {average(area_data['rejections']):.2f}\n")
            stats_writer.write(f"Average waiting time: {average(area_data['waiting_times']):.2f}\n")
            stats_writer.write(f"Average ride time (from meeting point to destination point): {average(area_data['ride_times']):.2f}\n")
            stats_writer.write(f"Average total ride time: {average(area_data['total_times']):.2f}\n")
            stats_writer.write(f"Average driver distance from the meeting point: {average(area_data['waiting_lengths']):.2f}\n")
            stats_writer.write(f"Average lengths from meeting point to destination point: {average(area_data['ride_lengths']):.2f}\n")
            stats_writer.write(f"Average total ride lenght: {average(area_data['total_lengths']):.2f}\n")
            stats_writer.write(f"Average expected price: {average(area_data['expected_prices']):.2f}\n")
            stats_writer.write(f"Average price: {average(area_data['prices']):.2f}\n")
            stats_writer.write(f"Average error on price prediction: {average(area_data['diff_prices']):.2f}\n")
            stats_writer.write(f"Average error on waiting time prediction: {average(area_data['diff_waiting_times']):.2f}\n")
            stats_writer.write(f"Average error on ride time prediction: {average(area_data['diff_ride_times']):.2f}\n")
            stats_writer.write(f"Average error on total time prediction: {average(area_data['diff_total_times']):.2f}\n")
            stats_writer.write(f"Average error on driver distance from the meeting point: {average(area_data['diff_waiting_lengths']):.2f}\n")
            stats_writer.write(f"Average error on lengths from meeting point to destination point prediction: {average(area_data['diff_ride_times']):.2f}\n")
            stats_writer.write(f"Average error on total ride lenght prediction: {average(area_data['diff_total_lengths']):.2f}\n")
            stats_writer.write('-'*9)
            stats_writer.write(f"\nCUSTOMER PROBABILITY DISTRIBUTION\n")
            stats_writer.write('-'*9)
            stats_writer.write('\n')
            customer_personality_counter = 0
            for threshold, personality in area_data["customer_personality_probability_distribution"]:
                if (customer_personality_counter == 0):
                    stats_writer.write(f"Generation of {personality} customer, with probability {threshold:.2f}\n")
                else:
                    previous_threshold = area_data["customer_personality_probability_distribution"][customer_personality_counter][0]
                    stats_writer.write(f"Generation of {personality} customer, with probability {(threshold - previous_threshold):.2f}\n")
                customer_personality_counter += 1
            stats_writer.write('-'*9)

            stats_writer.write(f"\nDRIVER PROBABILITY DISTRIBUTION\n")
            stats_writer.write('-'*9)
            stats_writer.write('\n')
            driver_personality_counter = 0
            for threshold, personality in area_data["driver_personality_probability_distribution"]:
                if (driver_personality_counter == 0):
                    stats_writer.write(f"Generation of {personality} driver, with probability {threshold:.2f}\n")
                else:
                    previous_threshold = area_data["driver_personality_probability_distribution"][driver_personality_counter][0]
                    stats_writer.write(f"Generation of {personality} driver, with probability {(threshold - previous_threshold):.2f}\n")
                driver_personality_counter += 1
            stats_writer.write('-'*9)
            stats_writer.write('\n')

            uber_stats["completed"].append(area_data['completed'])
            uber_stats["canceled"].append(area_data['canceled'])
            uber_stats["average_waiting_times"].append(average(area_data['waiting_times']))
            uber_stats["average_ride_times"].append(average(area_data['ride_times']))
            uber_stats["average_total_times"].append(average(area_data['total_times']))
            uber_stats["average_waiting_lengths"].append(average(area_data['waiting_lengths']))
            uber_stats["average_ride_lengths"].append(average(area_data['ride_lengths']))
            uber_stats["average_total_lengths"].append(average(area_data['total_lengths']))
            uber_stats["average_expected_prices"].append(average(area_data['expected_prices']))
            uber_stats["average_prices"].append(average(area_data['prices']))
            uber_stats["average_diff_prices"].append(average(area_data['diff_prices']))
            uber_stats["average_diff_waiting_times"].append(average(area_data['diff_waiting_times']))
            uber_stats["average_diff_ride_times"].append(average(area_data['diff_ride_times']))
            uber_stats["average_diff_total_times"].append(average(area_data['diff_total_times']))
            uber_stats["average_diff_waiting_lengths"].append(average(area_data['diff_waiting_lengths']))
            uber_stats["average_diff_ride_lengths"].append(average(area_data['diff_ride_times']))
            uber_stats["average_diff_total_lengths"].append(average(area_data['diff_total_lengths']))
            uber_stats["average_rejections"].append(average(area_data['rejections']))
            uber_stats["average_surge_multipliers"].append(average(area_data['surge_multipliers']))
            uber_stats["average_balances"].append(average(area_data['balances']))

        stats_writer.write("\n")
        stats_writer.write("*"*17)
        stats_writer.write("\nGLOBAL STATISTICS\n")
        stats_writer.write("*"*17)
        stats_writer.write('\n')
        stats_writer.write(f"Rides Canceled: {sum(uber_stats['canceled'])}\n")
        stats_writer.write(f"Rides completed: {sum(uber_stats['completed'])}\n")
        stats_writer.write(f"Average Rejections: {average(uber_stats['average_rejections']):.2f}\n")
        stats_writer.write(f"Average waiting time: {average(uber_stats['average_waiting_times']):.2f}\n")
        stats_writer.write(f"Average ride time (from meeting point to destination point): {average(uber_stats['average_ride_times']):.2f}\n")
        stats_writer.write(f"Average total ride time: {average(uber_stats['average_total_times']):.2f}\n")
        stats_writer.write(f"Average driver distance from the meeting point: {average(uber_stats['average_waiting_lengths']):.2f}\n")
        stats_writer.write(f"Average lengths from meeting point to destination point: {average(uber_stats['average_ride_lengths']):.2f}\n")
        stats_writer.write(f"Average total ride lenght: {average(uber_stats['average_total_lengths']):.2f}\n")
        stats_writer.write(f"Average expected price: {average(uber_stats['average_expected_prices']):.2f}\n")
        stats_writer.write(f"Average price: {average(uber_stats['average_prices']):.2f}\n")
        stats_writer.write(f"Average error on price prediction: {average(uber_stats['average_diff_prices']):.2f}\n")
        stats_writer.write(f"Average error on waiting time prediction: {average(uber_stats['average_diff_waiting_times']):.2f}\n")
        stats_writer.write(f"Average error on ride time prediction: {average(uber_stats['average_diff_ride_times']):.2f}\n")
        stats_writer.write(f"Average error on total time prediction: {average(uber_stats['average_diff_total_times']):.2f}\n")
        stats_writer.write(f"Average error on driver distance from the meeting point: {average(uber_stats['average_diff_waiting_lengths']):.2f}\n")
        stats_writer.write(f"Average error on lengths from meeting point to destination point prediction: {average(uber_stats['average_diff_ride_times']):.2f}\n")
        stats_writer.write(f"Average error on total ride lenght prediction: {average(uber_stats['average_diff_total_lengths']):.2f}\n")
        stats_writer.write(f"Average surge multiplier: {average(uber_stats['average_surge_multipliers']):.2f}\n")
        stats_writer.write(f"Average balance: {average(uber_stats['average_balances']):.2f}\n")           

def save_global_statistics(step,ride):
    #print("save_simulation_statistics")

    global uber_stats, row_index

    old_uber_stats = copy(uber_stats)
    uber_stats = init_uber_stats()

    with open(f"global_indicators_{time_simulation}", 'a', newline='\n') as out_file:
        stats_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for area_id, area_data in areas.items():
            uber_stats["completed"].append(area_data['completed'])
            uber_stats["canceled"].append(area_data['canceled'])
            uber_stats["average_waiting_times"].append(average(area_data['waiting_times']))
            uber_stats["average_ride_times"].append(average(area_data['ride_times']))
            uber_stats["average_total_times"].append(average(area_data['total_times']))
            uber_stats["average_waiting_lengths"].append(average(area_data['waiting_lengths']))
            uber_stats["average_ride_lengths"].append(average(area_data['ride_lengths']))
            uber_stats["average_total_lengths"].append(average(area_data['total_lengths']))
            uber_stats["average_expected_prices"].append(average(area_data['expected_prices']))
            uber_stats["average_prices"].append(average(area_data['prices']))
            uber_stats["average_diff_prices"].append(average(area_data['diff_prices']))
            uber_stats["average_diff_waiting_times"].append(average(area_data['diff_waiting_times']))
            uber_stats["average_diff_ride_times"].append(average(area_data['diff_ride_times']))
            uber_stats["average_diff_total_times"].append(average(area_data['diff_total_times']))
            uber_stats["average_diff_waiting_lengths"].append(average(area_data['diff_waiting_lengths']))
            uber_stats["average_diff_ride_lengths"].append(average(area_data['diff_ride_times']))
            uber_stats["average_diff_total_lengths"].append(average(area_data['diff_total_lengths']))
            uber_stats["average_rejections"].append(average(area_data['rejections']))
            uber_stats["average_surge_multipliers"].append(average(area_data['surge_multipliers']))
            uber_stats["average_balances"].append(average(area_data['balances']))

        stats_writer.writerow([
            f"{step}",
            f"{sum(uber_stats['canceled'])}",
            f"{sum(uber_stats['completed'])}",
            f"{(sum(uber_stats['completed'])/(sum(uber_stats['canceled']) + sum(uber_stats['completed']))):.2f}",
            f"{average(uber_stats['average_rejections']):.2f}",
            f"{average(uber_stats['average_waiting_times']):.2f}",
            f"{average(uber_stats['average_ride_times']):.2f}",
            f"{average(uber_stats['average_total_times']):.2f}",
            f"{average(uber_stats['average_waiting_lengths']):.2f}",
            f"{average(uber_stats['average_ride_lengths']):.2f}",
            f"{average(uber_stats['average_total_lengths']):.2f}",
            f"{average(uber_stats['average_expected_prices']):.2f}",
            f"{average(uber_stats['average_prices']):.2f}",
            f"{average(uber_stats['average_diff_prices']):.2f}",
            f"{average(uber_stats['average_diff_waiting_times']):.2f}",
            f"{average(uber_stats['average_diff_ride_times']):.2f}",
            f"{average(uber_stats['average_diff_total_times']):.2f}",
            f"{average(uber_stats['average_diff_waiting_lengths']):.2f}",
            f"{average(uber_stats['average_diff_ride_times']):.2f}",
            f"{average(uber_stats['average_diff_total_lengths']):.2f}",
            f"{average(uber_stats['average_surge_multipliers']):.2f}",
            f"{average(uber_stats['average_balances']):.2f}"
        ])

    with open(f"hardiness_indicators_{time_simulation}", 'a', newline='\n') as out_file:
        stats_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        stats_writer.writerow([
            f"{step}",
            f"{sum(uber_stats['canceled'])}",
            f"{sum(uber_stats['completed'])}",
            f"{(sum(uber_stats['completed'])/(sum(uber_stats['canceled']) + sum(uber_stats['completed']))):.2f}",
            f"{average(uber_stats['average_rejections']):.2f}",
            f"{average(uber_stats['average_waiting_times']):.2f}",
            f"{average(uber_stats['average_ride_times']):.2f}",
            f"{average(uber_stats['average_total_times']):.2f}",
            f"{average(uber_stats['average_surge_multipliers']):.2f}",
        ])

    if (row_index > 0):
        with open(f"global_diff_indicators_{time_simulation}", 'a', newline='\n') as out_file:
            stats_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            stats_writer.writerow([
                f"{step}",
                f"{sum(uber_stats['canceled']) - sum(old_uber_stats['canceled'])}",
                f"{sum(uber_stats['completed']) - sum(old_uber_stats['completed'])}",
                f"{(sum(uber_stats['completed'])/(sum(uber_stats['canceled']) + sum(uber_stats['completed'])) - sum(old_uber_stats['completed'])/(sum(old_uber_stats['canceled']) + sum(old_uber_stats['completed']))):.2f}",
                f"{(average(uber_stats['average_rejections']) - average(old_uber_stats['average_rejections'])):.2f}",
                f"{(average(uber_stats['average_waiting_times']) - average(old_uber_stats['average_waiting_times'])):.2f}",
                f"{(average(uber_stats['average_ride_times']) - average(old_uber_stats['average_ride_times'])):.2f}",
                f"{(average(uber_stats['average_total_times']) - average(old_uber_stats['average_total_times'])):.2f}",
                f"{(average(uber_stats['average_waiting_lengths']) - average(old_uber_stats['average_waiting_lengths'])):.2f}",
                f"{(average(uber_stats['average_ride_lengths']) - average(old_uber_stats['average_ride_lengths'])):.2f}",
                f"{(average(uber_stats['average_total_lengths']) - average(old_uber_stats['average_total_lengths'])):.2f}",
                f"{(average(uber_stats['average_expected_prices']) - average(old_uber_stats['average_expected_prices'])):.2f}",
                f"{(average(uber_stats['average_prices']) - average(old_uber_stats['average_prices'])):.2f}",
                f"{(average(uber_stats['average_diff_prices']) - average(old_uber_stats['average_diff_prices'])):.2f}",
                f"{(average(uber_stats['average_diff_waiting_times']) - average(old_uber_stats['average_diff_waiting_times'])):.2f}",
                f"{(average(uber_stats['average_diff_ride_times']) - average(old_uber_stats['average_diff_ride_times'])):.2f}",
                f"{(average(uber_stats['average_diff_total_times']) - average(old_uber_stats['average_diff_total_times'])):.2f}",
                f"{(average(uber_stats['average_diff_waiting_lengths']) - average(old_uber_stats['average_diff_waiting_lengths'])):.2f}",
                f"{(average(uber_stats['average_diff_ride_times']) - average(old_uber_stats['average_diff_ride_times'])):.2f}",
                f"{(average(uber_stats['average_diff_total_lengths']) - average(old_uber_stats['average_diff_total_lengths'])):.2f}",
                f"{(average(uber_stats['average_surge_multipliers']) - average(old_uber_stats['average_surge_multipliers'])):.2f}",
                f"{(average(uber_stats['average_balances']) - average(old_uber_stats['average_balances'])):.2f}"
            ])
    
    row_index += 1


def save_ride_stats(ride):
    #print("save_ride_stats")
    with open(f"output_file_{time_simulation}",'a', newline='') as out_file:
        out_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        out_writer.writerow([
            ride["end_step"],
            "%.2f" % ride["ride_length"],
            "%.2f" % ride["waiting_length"],
            "%.2f" % ride["total_length"],
            "%.2f" % ride["expected_waiting_time"],
            "%.2f" % ride["expected_ride_time"],
            "%.2f" % ride["expected_total_time"],
            "%.2f" % ride["expected_price"],
            "%.2f" % ride["waiting_time"],
            "%.2f" % ride["ride_time"],
            "%.2f" % ride["total_time"],
            "%.2f" % ride["price"],
            "%.2f" % ride["surge_multiplier"],
            ride["rejections"]
        ])


def average(lst):
    if (len(lst)) > 0:
        return sum(lst) / len(lst)
    return 0

def init_uber_stats():
    return {
        "canceled": [],
        "completed": [],
        "average_prices": [],
        "average_expected_prices": [],
        "average_waiting_times": [],
        "average_ride_times": [],
        "average_total_times": [],
        "average_waiting_lengths": [],
        "average_ride_lengths": [],
        "average_total_lengths": [],
        "average_diff_prices": [],
        "average_diff_waiting_times": [],
        "average_diff_ride_times": [],
        "average_diff_total_times": [],
        "average_diff_waiting_lengths": [],
        "average_diff_ride_lengths": [],
        "average_diff_total_lengths": [],
        "average_surge_multipliers": [],
        "average_balances": [],
        "average_rejections": []
    }


def init_edges_speed():
    edge_prefix = net_info["edge_prefix"]
    for i in range(net_info["min_edge_id"],net_info["max_edge_id"] + 1):
        traci.edge.setMaxSpeed(f"{edge_prefix}{i}", random.randrange(9,21))
        traci.edge.setMaxSpeed(f"-{edge_prefix}{i}", random.randrange(9,21))

def init_random_routes(route_prefix,min_id, max_id,num_routes, factor=5):
    edge_prefix = net_info["edge_prefix"]
    for i in range(num_routes):
        route_id = f"{route_prefix}_route_{i}"
        from_edge = random.randrange(min_id,max_id + 1)
        to_edge = random.randrange(min_id,max_id + 1)
        prefix_from = "" if random_choice(0.5) else "-"
        prefix_to = "" if random_choice(0.5) else "-"

        while(abs(to_edge - from_edge) < factor):
            to_edge = random.randrange(min_id,max_id)

        route_stage = traci.simulation.findRoute(f"{prefix_from}{edge_prefix}{from_edge}",f"{prefix_to}{edge_prefix}{to_edge}")
        traci.route.add(route_id,route_stage.edges)


def run(simulator):
    print('RUN')
    step = 0

    while True:
        traci.simulationStep()
        timestamp = traci.simulation.getTime()
        step += 1

        if (step % time_update_surge == 0):
            update_surge_multiplier()

        update_drivers(timestamp)
        update_drivers_area()
        update_rides_state(timestamp, step)

        if (step % time_driver_generation) == 0:
            for area_id, area_data in areas.items():
                for i in range(area_data["generation"]["many"][1]):
                    if (random_choice(area_data["generation"]["driver"])):
                        create_driver(timestamp, area_id)
    
        if (step % time_customer_generation) == 0:
            for area_id, area_data in areas.items():
                for i in range(area_data["generation"]["many"][0]):
                    if (random_choice(area_data["generation"]["customer"])):
                        #simulator.create_customer(timestamp,customer_id_counter, area_data)
                        create_customer(timestamp,area_id)
                        
        
        if (step % time_dispatch) == 0:
            dispatch_rides(timestamp)
             
        if (step % time_move) == 0:
            update_drivers_movements(timestamp)
        
        if (fault_simulation and step == fault_simulation_step):
            areas["A"]["generation"]["customer"] = 0.8
            areas["A"]["generation"]["many"] = (8,3)
            print("FAULTY")

        if (peak):
            for start, end in peak_simulation:
                if (step == start):
                    areas["A"]["generation"]["customer"] = 0.6
                    areas["B"]["generation"]["customer"] = 0.6
                    areas["C"]["generation"]["customer"] = 0.4
                    areas["D"]["generation"]["customer"] = 0.4
                    print("FAULTY")
                    
                if (step == end):
                    areas["A"]["generation"]["customer"] = 0.25
                    areas["B"]["generation"]["customer"] = 0.25
                    areas["C"]["generation"]["customer"] = 0.1
                    areas["D"]["generation"]["customer"] = 0.1
                    print("STOP FAULTY")
            
        if step == simulation_duration:
            save_simulation_statistics()
            break

        #print_area_stats()

    traci.close()
    sys.stdout.flush()


def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    options, args = optParser.parse_args()
    return options


if __name__ == "__main__":
    # first, generate the route file for this simulation
    options = get_options()
    # If you want to run this tutorial please uncomment following lines, that define the sumoBinary
    # and delete the line before traci.start, to use the gui
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    traci.start([sumoBinary, "-c", "net_config/sumo.sumocfg",
                 "--tripinfo-output", "net_config/tripinfo.xml"])  

    print('INIT')
    init_edges_speed()
    num_random_routes = net_info["num_random_routes"]
    for area_id, area_data in areas.items():
        print(f"GENERATE ROUTES WITHIN AREA {area_id}")
        init_random_routes(f"area_{area_id}",area_data["edges"][0],area_data["edges"][1],num_random_routes)

        for i in range(10):
            if (random_choice(area_data["generation"]["driver"])):
                create_driver(0, area_id)

        for i in range(10):
            if (random_choice(area_data["generation"]["customer"])):
                create_customer(0, area_id)

    print(f"GENERATE ROUTES INTER-AREAS")
    init_random_routes(f"inter_areas", net_info["min_edge_id"],net_info["max_edge_id"],num_random_routes*5,factor=150)

    print(f"INIT SIMULATOR")
    simulator = Simulator(traci)

    run(simulator)