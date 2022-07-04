from src.model_old.Area import Area

class Net:
    def __init__(self, info, areas):
        self.min_edge_num = info["min_edge_num"]
        self.max_edge_num = info["max_edge_num"]
        self.edge_prefix = info["edge_prefix"]
        self.num_random_routes = info["num_random_routes"]
        self.areas = self.__init_areas(areas)

    def __init_areas(self, areas):
        areas_dict = {}
        for area_id, area_data in areas.items():
            areas_dict[area_id] = Area(area_data)
        return areas_dict

    def __str__(self):
        net_str = '*'*3
        net_str += "\nNET\n"
        net_str += '*'*3
        net_str += '\n'
        net_str += f"min edge id: +-{self.edge_prefix}{self.min_edge_num}\n"
        net_str += f"min edge id: +-{self.edge_prefix}{self.min_edge_num}\n"
        net_str += f"random routes: {self.num_random_routes}\n"
        net_str += '-'*5
        net_str += "\nAREAS\n"
        net_str += '-'*5
        net_str += '\n'
        for area_id, area in self.areas.items():
            net_str += str(area)
        return net_str

    def edge_area(self, edge_id):
        #print("edge_area")
        for area_id, area in self.areas.items():
            edges_names = []
            for i in range(area.edges[0], area.edges[1]+1):
                edges_names.append(f"{self.edge_prefix}{i}")
                edges_names.append(f"-{self.edge_prefix}{i}")
            if (edge_id in edges_names):
                return area_id
        return ""

    def is_valid_edge(self, edge):
        if not (edge == "") and not (("gneJ" in edge) or ("-gneJ" in edge)):
            return True
        return False



