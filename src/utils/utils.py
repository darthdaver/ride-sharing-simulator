import random
import json
from pathlib import Path


def check_empty_intersection(lists):
    intersection_list = lists[0]
    for lst in lists[1:]:
        intersection_list = list(set(intersection_list) & set(lst))
    return True if len(intersection_list) == 0 else False


def list_average(lst):
    return sum(lst) / len(lst) if len(lst) > 0 else 0


def list_average_diff(lst1, lst2):
    lst_diff = []
    for i, el in enumerate(lst1):
        diff = el - lst2[i]
        lst_diff.append(diff)
    return list_average(lst_diff)


def lists_union(lists):
    flat_list = []
    for lst in lists:
        flat_list = flat_list + lst
    return flat_list


# Return a random choice with a certain probability
def random_choice(p=0.5):
    # print("random_choice")
    return random.random() < p


def random_value_from_range(min_value, max_value):
    return random.randint(min_value, max_value)


def read_setup(path):
    # net parameters
    with open(Path(path)) as setup_json:
        setup_obj = json.load(setup_json)
        return setup_obj