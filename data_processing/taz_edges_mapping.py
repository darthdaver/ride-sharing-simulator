import json
import xmltodict

def taz_xml_to_json():
    with open('data/sf_n_o_minimal_shp_poly.poi.xml', 'r') as taz_poly_file:
        taz_poly = taz_poly_file.read()
    with open('data/sf_n_o_minimal_shp_edges_districts.poi.xml', 'r') as taz_district_file:
        taz_district = taz_district_file.read()
    taz_poly_dict = xmltodict.parse(taz_poly)
    taz_district_dict = xmltodict.parse(taz_district)
    with open('data/sf_n_o_minimal_poly_dict.json', 'w') as taz_poly_dict_file:
        json.dump(taz_poly_dict["additional"]["poly"], taz_poly_dict_file)
    with open('data/sf_n_o_minimal_district_dict.json', 'w') as taz_district_dict_file:
        json.dump(taz_district_dict["tazs"]["taz"], taz_district_dict_file)
    return taz_poly_dict["additional"]["poly"], taz_district_dict["tazs"]["taz"]

def export_csv_disctrict_edges(taz_district_dict):
    content = "taz_id,edge_id\n"
    for taz in taz_district_dict:
        id = taz["@id"]
        edges = taz["@edges"].split(" ")
        for edge in edges:
            content += f"{id},{edge}\n"
    with open('data/sf_n_o_minimal_edge.csv', 'w') as taz_edge_file:
        taz_edge_file.write(content)

taz_poly_dict, taz_disctrict_dict = taz_xml_to_json()
export_csv_disctrict_edges(taz_disctrict_dict)