import os
from functools import reduce
from src.state.RideState import RideState
from functools import reduce

class Printer:

    def __init__(self):
        self.__global_indicators_content = ""
        self.__global_indicators_content_v2 = ""
        self.__specific_indicators_content = ""
        self.__surge_multipliers_content = ""
        self.__rides_assignations_content = ""
        self.__areas_info_agents_content = ""

    def export_global_indicators(self):
        path = f"{os.getcwd()}/output/global-indicators.csv"
        with open(path, 'w') as outfile:
            outfile.write(self.__global_indicators_content)

    def export_global_indicators_v2(self):
        path = f"{os.getcwd()}/output/global-indicators_v2.csv"
        with open(path, 'w') as outfile:
            outfile.write(self.__global_indicators_content)

    def export_specific_indicators(self):
        path = f"{os.getcwd()}/output/specific-indicators.csv"
        with open(path, 'w') as outfile:
            outfile.write(self.__specific_indicators_content)

    def export_surge_multipliers(self):
        path = f"{os.getcwd()}/output/surge_multipliers.txt"
        with open(path, 'w') as outfile:
            outfile.write(self.__surge_multipliers_content)

    def export_rides_assignations(self):
        path = f"{os.getcwd()}/output/ride_assignations.txt"
        with open(path, 'w') as outfile:
            outfile.write(self.__rides_assignations_content)

    def export_areas_info_agents_statistics(self):
        path = f"{os.getcwd()}/output/areas_info_drivers.txt"
        with open(path, 'w') as outfile:
            outfile.write(self.__areas_info_agents_content)

    @staticmethod
    def export_areas_info(timestamp, areas_info):
        content = "*" * 20 + "\n"
        content += f"TIMESTAMP: {timestamp}\n"
        content += "-" * 20 + "\n"
        content += "AREAS:\n"
        for id_area, area_info in areas_info.items():
            content += f"ID AREA: {id_area}\n"
            content += f"RIDES ACCOMPLISHED: {area_info['ended']}\n"
            content += f"RIDES NOT ACCOMPLISHED: {area_info['notAccomplished']}\n"
            content += f"RIDES REJECTED: {area_info['rejected']}\n"
            content += f"RIDES CANCELED: ${area_info['canceled']}\n"
            content += f"SURGE MULTIPLIER: ${round(area_info['surgeMultipliers'][0], 2)}\n"
            content += f"BALANCE: ${area_info['ended']}\n"
        content += "*" * 20 + "\n\n"
        path = f"{os.getcwd()}/output/areas.txt"
        with open(path, 'a') as outfile:
            outfile.write(content)

    @staticmethod
    def export_customers_info(timestamp, customers_info):
        content = "*" * 20 + "\n"
        content += f"TIMESTAMP: {timestamp}\n"
        content += "-" * 20 + "\n"
        content += "INFO:\n"
        for id_customer, customer_info in customers_info.items():
            content += f"ID CUSTOMER: {id_customer}\n"
            content += f"STATE: {customer_info['state']}\n"
            content += f"PERSONALITY: {customer_info['personality']}\n"
            content += f"CURRENT LATITUDE: ${customer_info['current_coordinates'][0]}\n"
            content += f"CURRENT LONGITUDE: ${customer_info['current_coordinates'][1]}\n"
            content += "*" * 20 + "\n"
        path = f"{os.getcwd()}/output/{id_customer}.txt"
        with open(path, 'a') as outfile:
            outfile.write(content)

    @staticmethod
    def export_drivers_info(timestamp, drivers_info):
        content = "*" * 20 + "\n"
        content += f"TIMESTAMP: {timestamp}\n"
        content += "-" * 20 + "\n"
        content += "INFO:\n"
        for id_driver, driver_info in drivers_info.items():
            content += f"ID CUSTOMER: {id_driver}\n"
            content += f"STATE: {driver_info['state']}\n"
            content += f"PERSONALITY: {driver_info['personality']}\n"
            content += f"CURRENT LATITUDE: ${driver_info['current_coordinates'][0]}\n"
            content += f"CURRENT LONGITUDE: ${driver_info['current_coordinates'][1]}\n"
            content += "*" * 20 + "\n"
        path = f"{os.getcwd()}/output/{id_driver}.txt"
        with open(path, 'a') as outfile:
            outfile.write(content)

    @staticmethod
    def export_driver_movements(timestamp, driver_info, origin, destination):
        content = "*" * 20 + "\n"
        content += f"TIMESTAMP: {timestamp}\n";
        content += f"-" * 20 + "\n"
        content += f"MOVEMENT:\n"
        content += f"ID DRIVER: {driver_info['id']}\n"
        content += f"ORIGIN AREA {origin}\n"
        content += f"DESTINATION AREA {destination}\n"
        content += "*" * 20 + '\n'
        path = f"{os.getcwd()}/output/driver_movements.txt"
        with open(path, 'a') as outfile:
            outfile.write(content)

    @staticmethod
    def export_energy_indexes(timestamp, energy_indexes, num_timestamps):
        timestamp_start = int(timestamp) - num_timestamps + 1
        content = ""
        content_values = ""
        if timestamp == 1.0:
            content += "timestamp,unserved_request,unserved_requests_accepted,avg_overhead,avg_price_fluctuation\n"
            content_values += "timestamp,canceled,not_accomplished,requested,ended\n"
        else:
            accepted = 0
            not_accomplished = 0
            canceled = 0
            requested = 0
            sum_overhead = 0
            num_events_overhead = 0
            sum_price_fluctuation = 0
            num_events_price_fluctuation = 0

            for i in range(int(timestamp_start), int(timestamp) + 1):
                accepted += energy_indexes["accepted"][i]
                requested += energy_indexes["requested"][i]
                not_accomplished += energy_indexes["not_accomplished"][i]
                canceled += energy_indexes["canceled"][i]
                sum_overhead += reduce(lambda sum, o: sum + o, energy_indexes["overhead"][i], 0)
                num_events_overhead += len(energy_indexes["overhead"][i])
                sum_price_fluctuation += reduce(lambda sum, o: sum + o, energy_indexes["price_fluctuation"][i], 0)
                num_events_price_fluctuation += len(energy_indexes["price_fluctuation"][i])
            unserved_requests = (canceled + not_accomplished) / requested if requested else 0
            unserved_requests_accepted = (canceled + not_accomplished) / (canceled + not_accomplished + accepted) if (canceled + not_accomplished + accepted) else 0
            avg_overhead = sum_overhead / num_events_overhead if num_events_overhead > 0 else 0.0
            avg_price_fluctuation = sum_price_fluctuation / num_events_price_fluctuation if num_events_price_fluctuation > 0 else 0.0

            content += f"{timestamp},"
            content += f"{round(unserved_requests, 3)},"
            content += f"{round(unserved_requests_accepted, 3)},"
            content += f"{round(avg_overhead, 3)},"
            content += f"{round(avg_price_fluctuation, 3)}\n"
            content_values += f"{timestamp},{canceled},{not_accomplished},{requested},{num_events_overhead}\n"
        path = f"{os.getcwd()}/output/energy_indexes_{num_timestamps}.csv"
        path_value = f"{os.getcwd()}/output/energy_indexes_{num_timestamps}_values.csv"
        with open(path, 'a') as outfile:
            outfile.write(content)
        with open(path_value, 'a') as outfile_value:
            outfile_value.write(content_values)

            #unserved_requests = (energy_indexes["canceled"] + energy_indexes["not_accomplished"]) / energy_indexes["requested"] if energy_indexes["requested"] else 0
            #unserved_requests_accepted = (energy_indexes["canceled"] + energy_indexes["not_accomplished"]) / (energy_indexes["canceled"] + energy_indexes["not_accomplished"] + energy_indexes["accepted"])  if (energy_indexes["canceled"] + energy_indexes["not_accomplished"] + energy_indexes["accepted"]) else 0
            #avg_overhead = reduce(lambda sum, o: sum + o, energy_indexes["overhead"], 0) / len(energy_indexes["overhead"]) if len(energy_indexes["overhead"]) else 0
            #avg_price_fluctuation = reduce(lambda sum, p: sum + p, energy_indexes["price_fluctuation"], 0) / len(energy_indexes["price_fluctuation"]) if len(energy_indexes["price_fluctuation"]) else 0


    def save_areas_info_agents(self, timestamp, statistics):
        content = "*" * 20 + "\n"
        content += f"TIMESTAMP: {timestamp}\n"
        content += "-" * 20 + "\n"
        content += f"ID AREA: {statistics['area_id']}\n"
        content += f"IDLE DRIVERS: {statistics['idle_drivers']}\n"
        content += f"RESPONDING DRIVERS: {statistics['responding_drivers']}\n"
        content += f"PICKUP DRIVERS: {statistics['pickup_drivers']}\n"
        content += f"ON ROAD DRIVERS: {statistics['on_road_drivers']}\n"
        content += f"MOVING DRIVERS: {statistics['moving_drivers']}\n"
        content += f"ACTIVE CUSTOMERS: {statistics['active_customers']}\n"
        content += f"PENDING CUSTOMERS: {statistics['pending_customers']}\n"
        content += f"PICKUP CUSTOMERS: {statistics['pickup_customers']}\n"
        content += f"ON ROAD CUSTOMERS: {statistics['on_road_customers']}\n"
        content += f"BALANCE: {statistics['balance']}\n"
        self.__areas_info_agents_content += content

    def save_global_indicators(self, timestamp, rides_info):
        content = ""
        if timestamp == 1:
            content += "timestamp,"
            content += "rides_canceled,"
            content += "rides_not_accomplished,"
            content += "rides_completed,"
            content += "rides_in_progress,"
            content += "rides_accepted,"
            content += "rides_pending,"
            content += "total_rides,"
            content += "percentage_in_progress,"
            content += "percentage_rides_completed,"
            content += "average_driver_rejections,"
            content += "average_expected_waiting_time,"
            content += "average_expected_ride_time,"
            content += "average_expected_total_time,"
            content += "average_waiting_time,"
            content += "average_ride_time,"
            content += "average_total_time,"
            content += "average_meeting_length,"
            content += "average_length,"
            content += "average_total_length,"
            content += "average_expected_meeting_length,"
            content += "average_expected_ride_length,"
            content += "average_expected_total_length,"
            content += "average_expected_price,"
            content += "average_price,"
            content += "average_error_price,"
            content += "average_error_waiting_time,"
            content += "average_error_ride_time,"
            content += "average_error_total_time,"
            content += "average_error_meeting_length,"
            content += "average_error_ride_length,"
            content += "average_error_total_length,"
            content += "average_surge_multiplier"
            content += "\n"
        rides_canceled = list(filter(lambda r: r["state"] in [RideState.CANCELED], rides_info))
        rides_not_accomplished = list(filter(lambda r: r["state"] in [RideState.NOT_ACCOMPLISHED], rides_info))
        rides_accepted = list(filter(lambda r: r["state"] in [RideState.PICKUP, RideState.ON_ROAD, RideState.END], rides_info))
        rides_pending = list(filter(lambda r: r["state"] == RideState.PENDING, rides_info))
        rides_in_progress = list(filter(lambda r: r["state"] in [RideState.PICKUP, RideState.ON_ROAD], rides_info))
        rides_completed = list(filter(lambda r: r["state"] == RideState.END, rides_info))
        rides_requested = list(filter(lambda r: r["state"] == RideState.REQUESTED, rides_info))
        rides_simulation_error = list(filter(lambda r: r["state"] == RideState.SIMULATION_ERROR, rides_info))
        rides_set = list(filter(lambda r: r["state"] in [RideState.PENDING, RideState.END, RideState.ON_ROAD, RideState.PICKUP, RideState.NOT_ACCOMPLISHED, RideState.CANCELED], rides_info))
        rides_confirmed = list(filter(lambda r: r["state"] in [RideState.PICKUP, RideState.ON_ROAD, RideState.END], rides_info))
        rides_waiting_completed = list(filter(lambda r: r["state"] in [RideState.ON_ROAD, RideState.END], rides_info))
        percentage_not_accomplished = len(rides_not_accomplished) / (len(rides_not_accomplished) + len(rides_confirmed)) if (len(rides_confirmed) + len(rides_not_accomplished)) > 0 else 0
        percentage_canceled = len(rides_canceled) / (len(rides_canceled) + len(rides_confirmed)) if (len(rides_confirmed) + len(rides_confirmed)) > 0 else 0
        percentage_completed = len(rides_completed) / (len(rides_completed) + len(rides_not_accomplished) + len(rides_canceled)) if (len(rides_completed) + len(rides_not_accomplished) + len(rides_canceled)) > 0 else 0
        percentage_in_progress = len(rides_accepted) / (len(rides_accepted) + len(rides_not_accomplished) + len(rides_canceled)) if (len(rides_accepted) + len(rides_not_accomplished) + len(rides_canceled)) > 0 else 0
        average_driver_rejections = reduce(lambda sum, r: sum + len(r["request"]["rejections"]), rides_info, 0) / len(rides_set) if len(rides_set) > 0 else 0
        average_expected_waiting_time = reduce(lambda sum, r: sum + r["stats"]["expected_meeting_duration"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0
        average_expected_ride_time = reduce(lambda sum, r: sum + r["stats"]["expected_ride_duration"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0
        average_expected_total_time = reduce(lambda sum, r: sum + r["stats"]["expected_meeting_duration"] + r["stats"]["expected_ride_duration"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0
        average_waiting_time = reduce(lambda sum, r: sum + r["stats"]["meeting_duration"], rides_waiting_completed, 0) / len(rides_waiting_completed) if len(rides_waiting_completed) > 0 else 0
        average_ride_time = reduce(lambda sum, r: sum + r["stats"]["ride_duration"], rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_total_time = reduce(lambda sum, r: sum + r["stats"]["meeting_duration"] + r["stats"]["ride_duration"], rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_meeting_length = reduce(lambda sum, r: sum + r["stats"]["meeting_length"], rides_waiting_completed, 0) / len(rides_waiting_completed) if len(rides_waiting_completed) > 0 else 0
        average_ride_length = reduce(lambda sum, r: sum + r["stats"]["ride_length"], rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_total_length = reduce(lambda sum, r: sum + r["stats"]["meeting_length"] + r["stats"]["ride_length"], rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_expected_meeting_length = reduce(lambda sum, r: sum + r["stats"]["expected_meeting_length"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0
        average_expected_ride_length = reduce(lambda sum, r: sum + r["stats"]["expected_ride_length"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0
        average_expected_total_length = reduce(lambda sum, r: sum + r["stats"]["expected_meeting_length"] + r["stats"]["expected_ride_length"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0
        average_expected_price = reduce(lambda sum, r: sum + r["stats"]["expected_price"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0
        average_price = reduce(lambda sum, r: sum + r["stats"]["price"], rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_error_price = reduce(lambda sum, r: sum + (r["stats"]["price"] - r["stats"]["expected_price"])**2, rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_error_waiting_time = reduce(lambda sum, r: sum + (r["stats"]["meeting_duration"] - r["stats"]["expected_meeting_duration"])**2, rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_error_ride_time = reduce(lambda sum, r: sum + (r["stats"]["ride_duration"] - r["stats"]["expected_ride_duration"])**2, rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_error_total_time = reduce(lambda sum, r: sum + ((r["stats"]["meeting_duration"] + r["stats"]["ride_duration"]) - (r["stats"]["expected_meeting_duration"] + r["stats"]["expected_ride_duration"]))**2, rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_error_meeting_length = reduce(lambda sum, r: sum + (r["stats"]["meeting_length"] - r["stats"]["expected_meeting_length"]) ** 2, rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_error_ride_length = reduce(lambda sum, r: sum + (r["stats"]["ride_length"] - r["stats"]["expected_ride_length"]) ** 2, rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_error_total_length = reduce(lambda sum, r: sum + ((r["stats"]["meeting_length"] + r["stats"]["ride_length"]) - (r["stats"]["expected_meeting_length"] + r["stats"]["expected_ride_length"])) ** 2, rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_surge_multipliers = reduce(lambda sum, r: sum + r["stats"]["surge_multiplier"], rides_confirmed, 0) / len(rides_confirmed) if len(rides_confirmed) > 0 else 0

        content += f"{timestamp},"
        content += f"{len(rides_canceled)},"
        content += f"{len(rides_not_accomplished)},"
        content += f"{len(rides_completed)},"
        content += f"{len(rides_in_progress)},"
        content += f"{len(rides_accepted)},"
        content += f"{len(rides_pending)},"
        content += f"{len(rides_canceled) + len(rides_not_accomplished) + len(rides_completed) + len(rides_pending)},"
        content += f"{round(percentage_in_progress, 2)},"
        content += f"{round(percentage_completed, 2)},"
        content += f"{round(average_driver_rejections, 2)},"
        content += f"{round(average_expected_waiting_time, 2)},"
        content += f"{round(average_expected_ride_time, 2)},"
        content += f"{round(average_expected_total_time, 2)},"
        content += f"{round(average_waiting_time, 2)},"
        content += f"{round(average_ride_time, 2)},"
        content += f"{round(average_total_time, 2)},"
        content += f"{round(average_meeting_length, 2)},"
        content += f"{round(average_ride_length, 2)},"
        content += f"{round(average_total_length, 2)},"
        content += f"{round(average_expected_meeting_length, 2)},"
        content += f"{round(average_expected_ride_length, 2)},"
        content += f"{round(average_expected_total_length, 2)},"
        content += f"{round(average_expected_price, 2)},"
        content += f"{round(average_price, 2)},"
        content += f"{round(average_error_price, 2)},"
        content += f"{round(average_error_waiting_time, 2)},"
        content += f"{round(average_error_ride_time, 2)},"
        content += f"{round(average_error_total_time, 2)},"
        content += f"{round(average_error_meeting_length, 2)},"
        content += f"{round(average_error_ride_length, 2)},"
        content += f"{round(average_error_total_length, 2)},"
        content += f"{round(average_surge_multipliers, 2)}"
        content += "\n"
        self.__global_indicators_content += content

    def save_global_indicators_v2(self, timestamp, rides_info):
        content = ""
        if timestamp == 1:
            content += "timestamp,"
            content += "percentage_rides_canceled,"
            content += "percentage_rides_not_accomplished,"
            content += "percentage_accepted,"
            content += "percentage_pending,"
            content += "average_driver_rejections,"
            content += "average_expected_waiting_time,"
            content += "average_expected_waiting_time_vs_meeting_length,"
            content += "average_expected_ride_time_vs_length,"
            content += "average_expected_waiting_time_vs_average_waiting_time,"
            content += "average_waiting_time,"
            content += "average_waiting_time_vs_meeting_length,"
            content += "average_ride_time_vs_length,"
            content += "average_expected_meeting_length_vs_meeting_length,"
            content += "average_expected_ride_length_vs_ride_length,"
            content += "average_expected_price_vs_average_price,"
            content += "average_surge_multiplier"
            content += "\n"

        rides_canceled = list(filter(lambda r: r["state"] in [RideState.CANCELED], rides_info))
        rides_not_accomplished = list(filter(lambda r: r["state"] in [RideState.NOT_ACCOMPLISHED], rides_info))
        rides_accepted = list(filter(lambda r: r["state"] in [RideState.PICKUP, RideState.ON_ROAD, RideState.END], rides_info))
        rides_pending = list(filter(lambda r: r["state"] == RideState.PENDING, rides_info))
        rides_completed = list(filter(lambda r: r["state"] == RideState.END, rides_info))
        rides_set = list(filter(lambda r: r["state"] in [RideState.PENDING, RideState.END, RideState.ON_ROAD, RideState.PICKUP, RideState.NOT_ACCOMPLISHED, RideState.CANCELED], rides_info))
        rides_waiting_completed = list(filter(lambda r: r["state"] in [RideState.ON_ROAD, RideState.END], rides_info))

        percentage_canceled = len(rides_canceled) / (len(rides_set)) if (len(rides_set)) > 0 else 0
        percentage_not_accomplished = len(rides_not_accomplished) / (len(rides_set)) if (len(rides_set)) > 0 else 0
        percentage_accepted = len(rides_accepted) / (len(rides_set)) if (len(rides_set)) > 0 else 0
        percentage_pending = len(rides_pending) / (len(rides_set)) if (len(rides_set)) > 0 else 0
        average_driver_rejections = reduce(lambda sum, r: sum + len(r["request"]["rejections"]), rides_info, 0) / (len(rides_set)) if (len(rides_set)) > 0 else 0
        average_expected_waiting_time = reduce(lambda sum, r: sum + r["stats"]["expected_meeting_duration"], rides_accepted, 0) / len(rides_accepted) if len(rides_accepted) > 0 else 0
        average_expected_waiting_time_vs_meeting_length = reduce(lambda sum, r: sum + (r["stats"]["expected_meeting_duration"]/r["stats"]["expected_meeting_length"]), rides_accepted, 0) / len(rides_accepted) if len(rides_accepted) > 0 else 0
        average_expected_ride_time_vs_length = reduce(lambda sum, r: sum + (r["stats"]["expected_ride_duration"]/r["stats"]["expected_ride_length"]), rides_accepted, 0) / len(rides_accepted) if len(rides_accepted) > 0 else 0
        average_expected_waiting_time_vs_average_waiting_time = reduce(lambda sum, r: sum + (r["stats"]["expected_meeting_duration"]/r["stats"]["meeting_duration"]), rides_waiting_completed, 0) / len(rides_waiting_completed) if len(rides_waiting_completed) > 0 else 0
        average_waiting_time = reduce(lambda sum, r: sum + r["stats"]["meeting_duration"], rides_waiting_completed, 0) / len(rides_waiting_completed) if len(rides_waiting_completed) > 0 else 0
        average_waiting_time_vs_meeting_length = reduce(lambda sum, r: sum + (r["stats"]["meeting_duration"]/r["stats"]["meeting_length"]), rides_waiting_completed, 0) / len(rides_waiting_completed) if len(rides_waiting_completed) > 0 else 0
        average_ride_time_vs_length = reduce(lambda sum, r: sum + (r["stats"]["ride_duration"]/r["stats"]["ride_length"]), rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_expected_meeting_length_vs_meeting_length = reduce(lambda sum, r: sum + (r["stats"]["expected_meeting_length"]/r["stats"]["meeting_length"]), rides_waiting_completed, 0) / len(rides_waiting_completed) if len(rides_waiting_completed) > 0 else 0
        average_expected_ride_length_vs_ride_length = reduce(lambda sum, r: sum + (r["stats"]["expected_ride_length"]/r["stats"]["ride_length"]), rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_expected_price_vs_average_price = reduce(lambda sum, r: sum + (r["stats"]["expected_price"]/r["stats"]["expected_price"]), rides_completed, 0) / len(rides_completed) if len(rides_completed) > 0 else 0
        average_surge_multipliers = reduce(lambda sum, r: sum + r["stats"]["surge_multiplier"], rides_accepted, 0) / len(rides_accepted) if len(rides_accepted) > 0 else 0

        content += f"{int(timestamp)},"
        content += f"{round(percentage_canceled,4)},"
        content += f"{round(percentage_not_accomplished,4)},"
        content += f"{round(percentage_accepted,4)},"
        content += f"{round(percentage_pending,4)},"
        content += f"{round(average_driver_rejections,4)},"
        content += f"{round(average_expected_waiting_time,4)},"
        content += f"{round(average_expected_waiting_time_vs_meeting_length,4)},"
        content += f"{round(average_expected_ride_time_vs_length,4)},"
        content += f"{round(average_expected_waiting_time_vs_average_waiting_time,4)},"
        content += f"{round(average_waiting_time,4)},"
        content += f"{round(average_waiting_time_vs_meeting_length,4)},"
        content += f"{round(average_ride_time_vs_length,4)},"
        content += f"{round(average_expected_meeting_length_vs_meeting_length,4)},"
        content += f"{round(average_expected_ride_length_vs_ride_length,4)},"
        content += f"{round(average_expected_price_vs_average_price,4)},"
        content += f"{round(average_surge_multipliers,4)},"
        content += "\n"
        self.__global_indicators_content_v2 += content


    def save_ride_assignation(self, timestamp, ride_id, customer_id, driver_id):
        content = "*" * 20 + "\n"
        content += f"TIMESTAMP: {timestamp}\n";
        content += f"-" * 20 + "\n"
        content += f"RIDE ID: {ride_id}\n"
        content += f"DRIVER ID: {driver_id}\n"
        content += f"CUSTOMER ID: {customer_id}\n"
        content += "*" * 20 + '\n'
        self.__rides_assignations_content += content


    def save_specific_indicators(self, timestamp, ride_info = None):
        content = ""
        if ride_info is None:
            content += f"timestamp,"
            content += f"timestamp_request,"
            content += f"timestamp_accepted,"
            content += f"timestamp_on_road,"
            content += f"source_area_id,"
            content += f"destination_area_id,"
            content += f"ride_length,"
            content += f"meeting_length,"
            content += f"total_length,"
            content += f"expected_waiting_time,"
            content += f"expected_ride_time,"
            content += f"expected_total_time,"
            content += f"waiting_time,"
            content += f"ride_time,"
            content += f"total_time,"
            content += f"expected_ride_price,"
            content += f"ride_price,"
            content += f"surge_multiplier,"
            content += f"rejections,"
            content += f"error_price,"
            content += f"error_meeting_duration,"
            content += f"error_ride_duration,"
            content += f"error_total_duration,"
            content += f"error_meeting_length,"
            content += f"error_meeting_length,"
            content += f"error_ride_length,"
            content += f"error_total_length"
            content += f"\n"
            content += f"\n"
        else:
            content += f"{timestamp},"
            content += f"{ride_info['stats']['timestamp_request']},"
            content += f"{ride_info['stats']['timestamp_pickup']},"
            content += f"{ride_info['stats']['timestamp_on_road']},"
            content += f"{ride_info['stats']['source_area_id']},"
            content += f"{ride_info['stats']['destination_area_id']},"
            content += f"{round(ride_info['stats']['ride_length'], 2)},"
            content += f"{round(ride_info['stats']['meeting_length'], 2)},"
            content += f"{round(ride_info['stats']['meeting_length'] + ride_info['stats']['ride_length'], 2)},"
            content += f"{round(ride_info['stats']['expected_meeting_duration'], 2)},"
            content += f"{round(ride_info['stats']['expected_ride_duration'], 2)},"
            content += f"{round(ride_info['stats']['expected_meeting_duration'] + ride_info['stats']['expected_ride_duration'], 2)},"
            content += f"{round(ride_info['stats']['meeting_duration'], 2)},"
            content += f"{round(ride_info['stats']['ride_duration'], 2)},"
            content += f"{round(ride_info['stats']['meeting_duration'] + ride_info['stats']['ride_duration'], 2)},"
            content += f"{round(ride_info['stats']['expected_price'], 2)},"
            content += f"{round(ride_info['stats']['price'], 2)},"
            content += f"{round(ride_info['stats']['surge_multiplier'], 2)},"
            content += f"{len(ride_info['request']['rejections'])},"
            content += f"{round(ride_info['stats']['price'] - ride_info['stats']['expected_price'], 2)},"
            content += f"{round(ride_info['stats']['meeting_duration'] - ride_info['stats']['expected_meeting_duration'], 2)},"
            content += f"{round(ride_info['stats']['ride_duration'] - ride_info['stats']['expected_ride_duration'], 2)},"
            content += f"{round((ride_info['stats']['meeting_duration'] + ride_info['stats']['ride_duration']) - (ride_info['stats']['expected_meeting_duration'] + ride_info['stats']['expected_ride_duration']), 2)},"
            content += f"{round(ride_info['stats']['meeting_length'] - ride_info['stats']['expected_meeting_length'], 2)},"
            content += f"{round(ride_info['stats']['ride_length'] - ride_info['stats']['expected_ride_length'], 2)},"
            content += f"{round((ride_info['stats']['meeting_length'] + ride_info['stats']['ride_length']) - (ride_info['stats']['expected_meeting_length'] + ride_info['stats']['expected_ride_length']), 2)}"
            content += f"\n"
        self.__specific_indicators_content += content

    def save_surge_multipliers(self, timestamp, areas_info):
        content = "*" * 20 + "\n"
        content += f"TIMESTAMP: {timestamp}\n"
        content += "-" * 20 + "\n"
        content += "AREAS:\n"
        for id_area, area_info in areas_info.items():
            content += f"ID AREA: {id_area}\n"
            content += f"SURGE MULTIPLIER: {round(area_info['surge_multipliers'][0], 2)}\n"
            content += f"BALANCE: {round(area_info['balances'][0], 2)}\n"
        content += "*" * 20 + "\n"
        self.__surge_multipliers_content += content
