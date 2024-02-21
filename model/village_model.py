from typing import Tuple, OrderedDict


class VillageModel:
    def __init__(self, village: Tuple[str, OrderedDict]):
        self.id = village[0]
        self.config = village[1]
