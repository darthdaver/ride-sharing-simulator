# Folder structure

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


## Area Subfolder

### area{area_id}_all_{timestamp}.csv
Each row of the file contains the average statistics from the start of the simulation, for the considered area.


### area{area_id}_diff_checkpoint_{timestamp}.csv
Each row of the file contains the average statistics from the last checkpoint (i.e. the last ride considered in the computation of the previous row of the file), for the considered area.

### area{area_id}_union_{timestamp}.csv
It contains the row of both the previous file (probably it is meaningless).


## Net Subfolder

### net_all_{timestamp}.csv
Each row of the file contains the average statistics from the start of the simulation, averaging the values of all the areas (i.e. considering the entire net).


### net_diff_checkpoint_{timestamp}.csv
Each row of the file contains the average statistics from the last checkpoint (i.e. the last ride considered in the computation of the previous row of the file), averaging the values of all the areas (i.e. considering the entire net).

### net_union_{timestamp}.csv
It contains the row of both the previous file (probably it is meaningless).


## Ride Subfolder

### rides_file_{timestamp}.csv
it contains the statistics of all the rides completed.


## Headers

## header_area_net.csv
It contains the label of the columns of the the area and net files.

## header_rides.csv
It contains the label of the columns of the the ride file.