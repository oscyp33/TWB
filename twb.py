import logging
import os
import pathlib
import random
import sys
import time
import traceback

import coloredlogs

from core.extractors import Extractor
from core.request import WebWrapper
from game.config_manager import ConfigManager
from game.village import Village
from helpers.helpers import internet_online, print_sleep_info
from manager import VillageManager

coloredlogs.install(
    level=logging.DEBUG if "-q" not in sys.argv else logging.INFO,
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

os.chdir(os.path.dirname(os.path.realpath(__file__)))


class TWB:
    res = None
    villages = []
    wrapper = None
    should_run = True
    runs = 0

    def __init__(self):
        self.report_manager = None
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.defence_states = {}
        self.result_villages = None
        self.wrapper = WebWrapper(
            self.config["server"]["endpoint"],
            server=self.config["server"]["server"],
            endpoint=self.config["server"]["endpoint"],
            reporter_enabled=self.config["reporting"]["enabled"],
            reporter_constr=self.config["reporting"]["connection_string"],
        )
        self.wrapper.start()

    def run(self):
        for vid in self.config["villages"]:
            v = Village(wrapper=self.wrapper, village_id=vid)
            self.villages.append(v)

        while self.should_run:
            if not internet_online():
                self.wait_for_internet()
            else:
                config = self.config_manager.config
                self.config_manager.update_config_if_needed(config)
                self.run_villages(config)
                self.sleep_between_runs()

    def get_overview(self, config):
        result_get = self.wrapper.get_url("game.php?screen=overview_villages")

        has_new_villages = False
        if config["bot"].get("add_new_villages", False):
            self.result_villages = Extractor.village_ids_from_overview(result_get)
            for found_vid in self.result_villages:
                if found_vid not in config["villages"]:
                    logging.info(
                        "Village %s was found but no config entry was found. Adding automatically"
                        % found_vid
                    )
                    self.config_manager.add_village(vid=found_vid)
                    has_new_villages = True
            if has_new_villages:
                return self.get_overview(self.config())

        return self.result_villages, result_get, config

    def get_world_options(self, overview_page, config):
        options_to_check = [
            ("flags_enabled", "screen=flags"),
            ("knight_enabled", "screen=statue"),
            ("boosters_enabled", "screen=inventory"),
            ("quests_enabled", "Quests.setQuestData"),
        ]

        changed = False
        for option, pattern in options_to_check:
            if config["world"][option] is None:
                changed = True
                if pattern in overview_page:
                    config["world"][option] = True
                else:
                    config["world"][option] = False

        return changed, config

    def is_active_hours(self, config):
        active_h = [int(x) for x in config["bot"]["active_hours"].split("-")]
        get_h = time.localtime().tm_hour
        return get_h in range(active_h[0], active_h[1])

    def wait_for_internet(self):
        logging.info("Internet seems to be down, waiting till it's back online...")
        sleep_time = self.calculate_sleep_time()
        print_sleep_info(sleep_time)
        time.sleep(sleep_time)

    def calculate_sleep_time(self):
        sleep = 0
        if self.is_active_hours(self.config):
            sleep = self.config["bot"]["active_delay"]
        elif self.config["bot"]["inactive_still_active"]:
            sleep = self.config["bot"]["inactive_delay"]

        return sleep + random.randint(20, 120)

    def run_villages(self, config):
        _, res_text, config = self.get_overview(config)
        has_changed, new_cf = self.get_world_options(res_text.text, config)
        if has_changed:
            logging.info("Updated world options")
            config = self.config_manager.merge_configs(config, new_cf)
            self.config_manager.deploy_new_configuration(config)
        for village_number, village in enumerate(self.villages):
            self.manage_village(village, config, village_number)

    def manage_village(self, village, config, village_number):
        if self.result_villages and village.village_id not in self.result_villages:
            logging.info(
                f"Village {village.village_id} will be ignored because it is not available anymore"
            )
            return

        self.set_village_name_template(village, config, village_number)
        village.run(config=config)
        self.manage_defense_states(village)

    def set_village_name_template(self, village, config, vnum):
        if (
            "auto_set_village_names" in config["bot"]
            and config["bot"]["auto_set_village_names"]
        ):
            template = config["bot"]["village_name_template"]
            num_pad = f"%0{config['bot']['village_name_number_length']}d" % vnum
            template = template.replace("{num}", num_pad)
            village.village_set_name = template

    def manage_defense_states(self, village):
        if (
            village.get_config(
                section="units", parameter="manage_defence", default=False
            )
            and village.def_man
        ):
            self.defence_states[village.village_id] = (
                village.def_man.under_attack
                if village.def_man.allow_support_recv
                else False
            )

    def sleep_between_runs(self):
        sleep_time = self.calculate_sleep_time()
        print_sleep_info(sleep_time)
        VillageManager.farm_manager(verbose=True)
        time.sleep(sleep_time)

    def start(self):
        root_directory = pathlib.Path(__file__).parent
        (root_directory / "cache").mkdir(exist_ok=True)
        (root_directory / "cache" / "attacks").mkdir(exist_ok=True)
        (root_directory / "cache" / "reports").mkdir(exist_ok=True)
        (root_directory / "cache" / "villages").mkdir(exist_ok=True)
        (root_directory / "cache" / "world").mkdir(exist_ok=True)
        (root_directory / "cache" / "logs").mkdir(exist_ok=True)
        (root_directory / "cache" / "managed").mkdir(exist_ok=True)
        (root_directory / "cache" / "hunter").mkdir(exist_ok=True)

        self.run()


for x in range(3):
    t = TWB()
    try:
        t.start()
    except Exception as e:
        t.wrapper.reporter.report(0, "TWB_EXCEPTION", str(e))
        print("I crashed :(   %s" % str(e))
        traceback.print_exc()
