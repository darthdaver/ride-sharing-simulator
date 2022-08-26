class EnergyIndexes:
    def __init__(self):
        self.__requested = { k: 0 for k in range(1,5001)}
        self.__canceled = { k: 0 for k in range(1,5001)}
        self.__accepted = { k: 0 for k in range(1,5001)}
        self.__not_accomplished = { k: 0 for k in range(1,5001)}
        self.__overhead = { k: [] for k in range(1,5001)}
        self.__price_fluctuation = { k: [] for k in range(1,5001)}

    def get_energy_indexes(self):
        return {
            "requested": self.__requested,
            "canceled": self.__canceled,
            "accepted": self.__accepted,
            "not_accomplished": self.__not_accomplished,
            "overhead": self.__overhead,
            "price_fluctuation": self.__price_fluctuation
        }

    def received_request(self, timestamp):
        self.__requested[int(timestamp)] += 1

    def accepted_request(self, timestamp):
        self.__accepted[int(timestamp)] += 1

    def canceled_request(self, timestamp):
        self.__canceled[int(timestamp)] += 1

    def request_not_accomplished(self, timestamp):
        self.__not_accomplished[int(timestamp)] += 1

    def compute_ovehead(self, timestamp_end, timestamp_request, estimated_ride_time):
        overhead = ((timestamp_end - timestamp_request) - estimated_ride_time) / estimated_ride_time
        self.__overhead[int(timestamp_end)].append(overhead)

    def compute_price_fluctuation(self, timestamp, actual_price, estimated_price):
        price_fluctuation = abs(actual_price - estimated_price) / estimated_price
        self.__price_fluctuation[int(timestamp)].append(price_fluctuation)
