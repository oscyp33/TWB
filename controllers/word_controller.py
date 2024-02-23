import logging
import time
from bs4 import BeautifulSoup
from core.extractors import Extractor
from core.request import WebWrapper
from pages.overview import OverviewPage


class WorldController:
    def __init__(self, world_model, config_manager, wrapper):
        self.logger = logging.getLogger(__name__)
        self.result_villages = None
        self.world_model = world_model
        self.config_manager = config_manager
        self.config = config_manager.config
        self.set_active_hours()
        self.wrapper = wrapper

    def run(self):
        """run the controller. This is a placeholder."""
        pass

    def set_active_hours(self):
        active_h = [int(x) for x in self.config["bot"]["active_hours"].split("-")]
        get_h = time.localtime().tm_hour
        self.world_model.is_active_hours = get_h in range(active_h[0], active_h[1])

    def get_overview(self, config):
        has_new_villages = False
        while config["bot"].get("add_new_villages", False):
            result_get = self.wrapper.get_url("game.php?screen=overview_villages")
            soup = BeautifulSoup(result_get.text, 'html.parser')
            self.result_villages = Extractor.village_ids_from_overview(result_get)
            overview_page = OverviewPage(self.wrapper)
            table = overview_page.production_table_data
            for found_vid in self.result_villages:
                if found_vid not in config["villages"]:
                    logging.info(
                        "Village %s was found but no config entry was found. Adding automatically"
                        % found_vid
                    )
                    self.config_manager.add_village(vid=found_vid)
                    has_new_villages = True

            if not has_new_villages:
                break

            # Aktualizuj konfigurację
            config = self.config_manager.config

        return self.result_villages, result_get, config

    def get_world_options(self):
        world_options = ["flags_enabled", "knight_enabled", "boosters_enabled", "quests_enabled"]
        changed = False

        for option in world_options:
            if self.config["world"][option] is None:
                setattr(self.config["world"], option, getattr(self.overview_page, option))
                changed = True

        return changed

    def get_villages(self):
        return self.world_model.villages

    def get_village(self):
        """get village"""
        pass
