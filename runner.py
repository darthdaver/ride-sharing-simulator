# @file    runner.py
# @author  Davide
# @date    2021-04-30


from __future__ import absolute_import
from __future__ import print_function
from copy import copy
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

from src.controller.Simulator import Simulator

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

    traci.start(["sumo-gui", "-c", "net_config/sumo.sumocfg",
                 "--tripinfo-output", "net_config/tripinfo.xml"])
    print('INIT')
    simulator = Simulator()
    #simulator.init_scenario()
    print(f"INIT SIMULATOR")
    simulator.run()