import csv
import random

import numpy as np
from numpyencoder import NumpyEncoder
import json

data_generator = {}
timestamp_events = { k: { "customers": [], "drivers": [] } for k in range(1,5001)}

with open("../data/df_mov_mean_std_pick_drop_no_hour_sf_n_o.csv", 'r') as trips_file:
    csv_data_reader = csv.DictReader(trips_file)
    np.random.seed(123)

    for row in csv_data_reader:
        mov_id = row["movement_id"]
        pickups_mean = float(row["pickups_mean"]) if not row["pickups_mean"] == "" else 0
        pickups_std = float(row["pickups_std"]) if not row["pickups_std"] == "" else 0
        #customer_uniform_dist = sorted(np.random.uniform(1, 5000, round((pickups_mean)*1.4)).astype(int))
        customer_uniform_dist = sorted(np.random.uniform(1, 5000, round((pickups_mean/3))).astype(int))
        #driver_uniform_dist = sorted(np.random.uniform(1, 5000, round((pickups_mean)*1.4 + pickups_std/10)).astype(int))
        driver_uniform_dist = sorted(np.random.uniform(1, 5000, round((pickups_mean/3) + pickups_std/10)).astype(int))
        if random.random() < 0.71:
            driver_uniform_dist.insert(0, random.randint(1,11))
            driver_uniform_dist.pop()
        strike_drivers = list(filter(lambda d: d < 2000, driver_uniform_dist))
        data_generator[mov_id] = {
            "movement_id": mov_id,
            "pickups_mean": pickups_mean,
            "pickups_std": pickups_std,
            "customer_dist": customer_uniform_dist,
            "driver_dist": driver_uniform_dist
        }

        for c_event in customer_uniform_dist:
            timestamp_events[int(c_event)]["customers"].append(mov_id)
        for d_event in driver_uniform_dist:
            timestamp_events[int(d_event)]["drivers"].append(mov_id)

    with open("../data/c_d_generator_dist_sf_n_o.json", "w") as data_generator_file:
        json.dump(data_generator, data_generator_file, cls=NumpyEncoder, indent=4)
    with open("../data/timeline_gen_events_sf_n_o.json", "w") as timeline_generator_file:
        json.dump(timestamp_events, timeline_generator_file, cls=NumpyEncoder, indent=4)