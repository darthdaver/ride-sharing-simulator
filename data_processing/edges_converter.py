import csv
import re

edges = [["osm_way_id"]]

with open('../data/sf_n_o_minimal_edge.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
        else:
            edge_id = row[1]
            edge_id_clean = re.findall("[0-9]+", edge_id)[0]
            edges.append([edge_id_clean])
            line_count += 1

with open('../data/sf_n_o_minimal_clean_edge.csv', mode='w') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in edges:
        csv_writer.writerow(row)