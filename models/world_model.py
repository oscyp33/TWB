from typing import OrderedDict

from models.village_model import VillageModel


class WorldModel:
    def __init__(self):
        self.villages = []
        self.is_active_hours = False

    def add_villages(self, villages: OrderedDict):
        for village in villages.items():
            self.villages.append(VillageModel(village))

