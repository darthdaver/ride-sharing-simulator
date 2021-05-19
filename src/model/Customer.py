from src.model.Human import Human
from src.utils import utils

import random

class Customer(Human):
    def __init__(self, timestamp, id_num, area_id, edges, edges_prefix, personality_distribution):
        super().__init__(timestamp, f"customer_{id_num}", area_id, personality_distribution)
        from_edge, to_edge = self.__init_edges(edges, edges_prefix)
        self.from_edge = from_edge
        self.to_edge = to_edge
        self.current_edge = from_edge
        self.pos = 0


    def __init_edges(self, edges, edge_prefix):
        min_edge = edges[0]
        max_edge = edges[1]
        from_edge_num = random.randrange(min_edge, max_edge+1)
        to_edge_num = random.randrange(min_edge, max_edge+1)

        while from_edge_num == to_edge_num:
            to_edge_num = random.randrange(min_edge, max_edge+1)

        prefix_from = "" if utils.random_choice(0.5) else "-"
        prefix_to = "" if utils.random_choice(0.5) else "-"
        from_edge =  f'{prefix_from}{edge_prefix}{from_edge_num}'
        to_edge =  f'{prefix_to}{edge_prefix}{to_edge_num}'
        return (from_edge, to_edge)

    def __str__(self):
        #customer_str = '-'*8
        #customer_str += "\nCUSTOMER\n"
        #customer_str += '-'*8
        #customer_str += '\n'
        #customer_str += super().__str__()
        customer_str = super().__str__()
        customer_str += f"     from edge: {self.from_edge}\n"
        customer_str += f"     to edge: {self.to_edge}\n"
        customer_str += f"     initial position: {self.pos}\n"
        customer_str += f"     current edge: {self.current_edge}"
        #customer_str += '-'*8
        #customer_str += '\n'
        return customer_str

    def send_request(self):
        pass