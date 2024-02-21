import datetime
import logging
import random


class SleepTimeManager:

    def __init__(self, config, world_model):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.sleep_time = 0
        self.sleep_time_increase = self.config["sleep_time_increase"]
        self.date_time_next = None

    def get_sleep_time(self):
        return self.sleep_time


    def calculate_sleep_time(self):
        sleep = 0
        if self.is_active_hours(self.config):
            sleep = self.config["bot"]["active_delay"]
        elif self.config["bot"]["inactive_still_active"]:
            sleep = self.config["bot"]["inactive_delay"]

        self.sleep_time = sleep + random.randint(20, 120)

    def print_sleep_info(self):
        dtn = datetime.datetime.now()
        dt_next = dtn + datetime.timedelta(0, self.sleep_time)
        self.logger.info(
            f"Dead for {self.sleep_time / 60:.2f} minutes (next run at: {dt_next.time()})"
        )