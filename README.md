# Ride-Sharing Simulator
Ride-sharing simulator with SUMO, TraCI and Python.

## Introduction
The current repository constitutes the backend logic of a ride-sharing simulator. The logic interacts with [SUMO](https://sumo.dlr.de/docs/index.html) (a popular traffic generator and simulator) through [TraCI](https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html) an API interface specifically developed for Python (you can find the documentation [here](https://sumo.dlr.de/pydoc/traci.html)).

## Requirements

### SUMO Simulator
The project exploits the functionalities of [SUMO](https://sumo.dlr.de/docs/index.html). **SUMO** can be installed following the instructions provided in the official [installation guide](https://sumo.dlr.de/docs/Installing/index.html) (for Windows users there is an executable installer, while for macOS and Linux users it is necessary to use a command-line tool such as **Homebrew** and **apt-get**, respectively. Note that macOS users have to install and run [XQuartz](https://formulae.brew.sh/cask/xquartz#default) to run the Sumo-GUI). The installation process will instal on the local machine **SUMO** and all the accessory tools to generate and import maps in Sumo.

### Python 3

The logic of the ride-sharing simulator is written in **Python 3**. Therefore, a stable version of Python 3 (for example, 3.6 or more) is necessary to run the simulator.


## Run

To run the experiments, download the project, move in the main directory of the project and run the following command:

    python3 runner.py

The command will open a SUMO Graphical User Interface (SUMO GUI) and will upload the default map saved on the `net_config` directory of the project (`manhattan.net.xml`).

**Note** - For **macOS** users it could be necessary to execute **XQuartz** before running the afermentioned command.

To start the simulation click on the play icon, as shown in the following image.

![Start Simulation](/assets/sumoGUI_arrow.png)

To show the id of the drivers and the customers generated during the simulation, set the visibility of the person and vehicle ids, as shown in the following screenshots.

![Start Simulation](/assets/options.png)
![Show Person Ids](/assets/person_id_arrow.png)
![Show Vehicle Ids](/assets/vehicle_id_arrow.png)

To speed up or slow down the simulation, modify the value of the delay options.

The logic of the simulator divides the map in 4 different areas, as shown in the following figure:

![Map Areas](/assets/areas.png)

The simulation produces data that refers to KPIs related to the rides performed in each area of the map. The data are collected in the folder `output`, generated at runtime. The structure of the output folder and the meaning of each generated file is reported in the section **Output Structure** of this **README** file.


## Software Architecture

The main components of the projects are:

1. **SUMO GUI**: it represents the graphical user interface of **SUMO** the traffic generator and simulator.
2. **NetEdit**: it is the tool through which the map used for the simulation has been defined.
3. **TraCI**; it constitutes the **API Interface** through which the logic of the **ride-sharing simulator** can communicate with **SUMO**.
4. **Random Traffic Script**: generate random traffic in the simulation. In other words, it adds random noise to the simulation.
5. **JSON Setup Files**: they represents the files to configure the parameters of the **ride-sharing simulator**.

![Software architecture](/assets/software_architecture.png)

## Project Structure
The following graph show the structure of the given project. The graph list only the relevant files.

    |---- net_config
    |       |-- add.add.xml
    |       |-- manhattan.net.xml
    |       |-- random_trips.trips.xml
    |       |-- sumo.sumocfg
    |---- src
    |       |-- config
    |       |-- controller
    |       |-- model
    |       |-- scenario
    |       |-- state
    |       |-- utils
    |---- randomTrips.py
    |---- runner.py

### net_config

The folder `net_config` contains all the file necessary to configure the net and **SUMO** parameters of the simulation.

### src
The `src` folder contains the logic of the ride-sharing simulator.

    config

The config folder contains the ride-sharing parameters of the simulation. The `.json` files contained in it are read at the beginning of the simulation to setup the parameters of the simulator.

    controller

It contains the `Simulator` and the `Printer` classes. The first represents the core of the simulator (it manages the step of the simulation and control all the logic of the simulation and the actors involved in the simulation). Instead, the second is instanciated to save all the data produced during the simulation in different files (in the `output` folder).

    model

The `model` folder contains the class of all the components and agents involved in the simulation.

    scenario

It contains the logic and the setup files of different scenarios. One and only one scenario is performed in each simulation. The scenario to simulate is setup before the simulation. It is defined in the `simulator.json` file, contained in the `src/config` folder.

    state

Contains all the possible states of the different agents and components involved in the simulation.

    utils

It contains accessory generic functions used by the simulator and the other components during the simulation.

### random_trips.py

`random_trips.py` is a script to generate random traffic within the simulation. The output of the script is a file that contains the descriptions of all the vehicles introduced during the simulation and the route followed by each vehicle during the simulation (for more information, follow the [link](https://sumo.dlr.de/docs/Tools/Trip.html)). In our case, the generated file `random_trips.trips.xml` has been positioned within the folder `net_config`. The content of the file `sumo.sumoconfig` contained in the same folder links to the `random_trips.trips.xml` to generate the traffic during the simulation.

### runner.py

It represents the main file of the project. It is executed to start the simulator and open the SUMO GUI at the beginning of the simulation.


## Output Folder Structure

    |---- area
    |       |-- area_A_all_{timestamp}.csv
    |       |-- area_A_diff_checkpoint_{timestamp}.csv
    |       |-- area_A_union_{timestamp}.csv
    |       |-- area_B_all_{timestamp}.csv
    |       |-- area_B_diff_checkpoint_{timestamp}.csv
    |       |-- area_B_union_{timestamp}.csv
    |       |-- area_C_all_{timestamp}.csv
    |       |-- area_C_diff_checkpoint_{timestamp}.csv
    |       |-- area_C_union_{timestamp}.csv
    |       |-- area_D_all_{timestamp}.csv
    |       |-- area_D_diff_checkpoint_{timestamp}.csv
    |       |-- area_D_union_{timestamp}.csv
    |---- net
    |       |-- net_all_{timestamp}.csv
    |       |-- net_diff_checkpoint_{timestamp}.csv
    |       |-- net_union_{timestamp}.csv
    |---- rides
    |       |-- rides_file_{timestamp}.csv
    |---- header_area_net.csv
    |---- header_ride.csv


### Area Subfolder

    area{area_id}_all_{timestamp}.csv
    
Each row of the file contains the average statistics from the start of the simulation, for the considered area.

    area{area_id}_diff_checkpoint_{timestamp}.csv

Each row of the file contains the average statistics from the last checkpoint (i.e. the last ride considered in the computation of the previous row of the file), for the considered area.

    area{area_id}_union_{timestamp}.csv
It contains the row of both the previous file (probably it is meaningless).


### Net Subfolder

    net_all_{timestamp}.csv
Each row of the file contains the average statistics from the start of the simulation, averaging the values of all the areas (i.e. considering the entire net).


    net_diff_checkpoint_{timestamp}.csv
Each row of the file contains the average statistics from the last checkpoint (i.e. the last ride considered in the computation of the previous row of the file), averaging the values of all the areas (i.e. considering the entire net).

    net_union_{timestamp}.csv
It contains the row of both the previous file (probably it is meaningless).


### Ride Subfolder

    rides_file_{timestamp}.csv
It contains the statistics of all the rides completed.


### Headers

    header_area_net.csv
It contains the label of the columns of the the area and net files.

    header_rides.csv
It contains the label of the columns of the the ride file.