from os import name
from taxi_simulation_trial.src.utils.Utils import list_average
from src.utils.utils import utils

from pathlib import Path
import time
import calendar
import csv


class Printer:
    def __init__(self):
        gmt = time.gmtime()
        self.time_simulation = calendar.timegm(gmt)

    def save_areas_global_stats(self, areas):
        #print("save area global stats")
        for area_id, area in areas.items():
            last_checkpoint = area.stats["last_checkpoint"]
            all_simulation = [ utils.list_average(v) for k,v in area.stats.items() ]
            from_last_checkpoint = [ utils.list_average(v[last_checkpoint:]) for k,v in area.stats.items() ]
            
            files = [
                (f"area_{area_id}_diff_checkpoint_{self.time_simulation}", from_last_checkpoint),
                (f"area_{area_id}_all_{self.time_simulation}", all_simulation),
                (f"area_{area_id}_union_{self.time_simulation}", all_simulation + from_last_checkpoint)
            ]

            for n_f, row in files:
                with open(n_f,'a', newline='') as area_all_file:
                    a_w = csv.writer(area_all_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    a_w.writerow([ el if isinstance(el, int) else "%.2f" for el in row ])


    def save_net_global_stats(self, areas):
        net_all_simulation = []
        net_from_last_checkpoint = []
        num_areas = len(areas.items())

        #print("save net global stats")
        for area_id, area in areas.items():
            last_checkpoint = area.stats["last_checkpoint"]
            area_all_simulation = [ utils.list_average(v) for k,v in area.stats.items() ]
            area_last_checkpoint = [ utils.list_average(v[last_checkpoint:]) for k,v in area.stats.items() ]
            if (len(net_all_simulation) == 0):
                net_all_simulation = area_all_simulation
                net_from_last_checkpoint = area_last_checkpoint
            else:
                [sum(x) for x in zip(net_all_simulation, area_all_simulation)]

        net_all_simulation = [ el / num_areas for el in net_all_simulation ]
        net_from_last_checkpoint = [ el / num_areas for el in net_from_last_checkpoint ]
        
        files = [
            (f"net_diff_checkpoint_{self.time_simulation}", net_from_last_checkpoint),
            (f"net_all_{self.time_simulation}", net_all_simulation),
            (f"net_union_{self.time_simulation}", net_all_simulation + net_from_last_checkpoint)
        ]

        for n_f, row in files:
            with open(n_f,'a', newline='') as area_all_file:
                a_w = csv.writer(area_all_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                a_w.writerow([ el if isinstance(el, int) else "%.2f" for el in row ])

    
    def save_ride_stats(self, ride):
        #print("save ride stats")
        ride_row = [ el if isinstance(el, int) else "%.2f" for el in ride.stats ]
        with open(f"rides_file_{self.time_simulation}",'a', newline='') as ride_file:
            ride_file = csv.writer(ride_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            ride_file.writerow(ride_row)