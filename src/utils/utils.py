import random
import math
import json
from pathlib import Path


def random_choice(p=0.5):
    return random.random() < p


def random_int_from_range(min_int, max_int):
    return random.randint(min_int, max_int)


def read_setup(path):
    # net parameters
    with open(Path(path)) as setup_json:
        setup_obj = json.load(setup_json)
        return setup_obj


def select_from_distribution(distribution):
    p = random.random()
    min_value = 0
    for threshold, value in distribution:
        if min_value <= p <= threshold:
            return value
        min_value = threshold
    return select_from_list(distribution)[1]


def select_from_list(lst):
    lst_len = len(lst)
    idx = math.floor(random.random() * lst_len)
    return lst[idx]

