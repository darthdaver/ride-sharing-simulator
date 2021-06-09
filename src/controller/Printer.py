from src.utils import utils

from pathlib import Path
import os
import time
import calendar
import csv


class Printer:
    def __init__(self):
        gmt = time.gmtime()
        self.time_simulation = calendar.timegm(gmt)

    def save_header(self, path, row):
        if not os.path.exists(path):
            with open(path,'a', newline='') as header_file:
                ride_file = csv.writer(header_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                ride_file.writerow(row)

    def save_areas_global_stats(self, step, areas):
        #print("save area global stats")
        for area_id, area in areas.items():
            last_checkpoint = area.stats["last_checkpoint"]
            all_simulation = [ v if not isinstance(v, list) else utils.list_average(v) for k,v in area.stats.items() ]
            from_last_checkpoint = [ v if not isinstance(v, list) else utils.list_average(v[last_checkpoint:]) for k,v in area.stats.items() ]
            header_row = [ k for k,v in area.stats.items() ]
            header_path = Path(f"output/header_area_net.csv")
            
            files = [
                (Path(f"output/area/area_{area_id}_diff_checkpoint_{self.time_simulation}.csv"), from_last_checkpoint),
                (Path(f"output/area/area_{area_id}_all_{self.time_simulation}.csv"), all_simulation),
                (Path(f"output/area/area_{area_id}_union_{self.time_simulation}.csv"), all_simulation + from_last_checkpoint)
            ]

            self.save_header(header_path, header_row)

            for n_f, row in files:
                if not os.path.exists(Path("output/area")):
                    os.makedirs(Path("output/area"))
                with open(n_f,'a', newline='') as area_all_file:
                    if (".csv" in str(n_f)):
                        a_w = csv.writer(area_all_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        a_w.writerow([ str(el) if isinstance(el, int) else ("%.2f" % el) for el in row ])

            if not os.path.exists(header_path):
                with open(header_path,'a', newline='') as header_file:
                    ride_file = csv.writer(header_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    ride_file.writerow(header_row)
                        



    def save_net_global_stats(self, step, areas):
        net_all_simulation = []
        net_from_last_checkpoint = []
        num_areas = len(areas.items())

        #print("save net global stats")
        for area_id, area in areas.items():
            last_checkpoint = area.stats["last_checkpoint"]
            area_all_simulation = [ v if not isinstance(v, list) else utils.list_average(v) for k,v in area.stats.items() ]
            area_from_last_checkpoint = [ v if not isinstance(v, list) else utils.list_average(v[last_checkpoint:]) for k,v in area.stats.items() ]
            if (len(net_all_simulation) == 0):
                net_all_simulation = area_all_simulation
                net_from_last_checkpoint = area_from_last_checkpoint
            else:
                [sum(x) for x in zip(net_all_simulation, area_all_simulation)]

        net_all_simulation = [ el / num_areas for el in net_all_simulation ]
        net_from_last_checkpoint = [ el / num_areas for el in net_from_last_checkpoint ]
        
        files = [
            (Path(f"output/net/net_diff_checkpoint_{self.time_simulation}.csv"), net_from_last_checkpoint),
            (Path(f"output/net/net_all_{self.time_simulation}.csv"), net_all_simulation),
            (Path(f"output/net/net_union_{self.time_simulation}.csv"), net_all_simulation + net_from_last_checkpoint)
        ]

        for n_f, row in files:
            if not os.path.exists(Path("output/net")):
                os.makedirs(Path("output/net"))
            with open(n_f,'a', newline='') as area_all_file:
                a_w = csv.writer(area_all_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                a_w.writerow([ str(el) if isinstance(el, int) else ("%.2f" % el) for el in row ])

    
    def save_ride_stats(self, ride):
        #print("save ride stats")
        if not os.path.exists(Path("output/rides")):
            os.makedirs(Path("output/rides"))
        ride_row = [ str(el) if isinstance(el, int) else ("%.2f" % el) for k, el in ride.stats.items() ]
        header_row = [ k for k, el in ride.stats.items() ]
        header_path = Path(f"output/header_ride.csv")

        with open(f"output/rides/rides_file_{self.time_simulation}.csv",'a', newline='') as ride_file:
            ride_file = csv.writer(ride_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            ride_file.writerow(ride_row)

        self.save_header(header_path, header_row)