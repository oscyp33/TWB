import logging
import time

from core.extractors import Extractor


class WorldController:
    def __init__(self, world_model, config):
        self.logger = logging.getLogger(__name__)
        self.result_villages = None
        self.world_model = world_model
        self.config = config
        self.set_active_hours()

    def run(self):
        """run the controller. This is a placeholder."""
        pass

    def set_active_hours(self):
        active_h = [int(x) for x in self.config["bot"]["active_hours"].split("-")]
        get_h = time.localtime().tm_hour
        self.world_model.is_active_hours = get_h in range(active_h[0], active_h[1])

    def get_overview(self):
        result_get = self.wrapper.get_url("game.php?screen=overview_villages")

        has_new_villages = False
        if self.config["bot"].get("add_new_villages", False):
            self.result_villages = Extractor.village_ids_from_overview(result_get)
            for found_vid in self.result_villages:
                if found_vid not in self.config["villages"]:
                    self.logger.info(
                        "Village %s was found but no config entry was found. Adding automatically"
                        % found_vid
                    )
                    self.world_model.add_village(vid=found_vid)
                    has_new_villages = True
            if has_new_villages:
                return self.get_overview()

        return self.result_villages, result_get, config

    def get_villages(self):
        return self.world_model.villages

    def get_village(self):
        """get village"""
        pass
