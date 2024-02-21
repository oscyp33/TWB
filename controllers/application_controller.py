import asyncio
import logging
import random
import sys
import threading

from controllers.word_controller import WorldController
from game.config_manager import ConfigManager
from helpers.internet_connection import internet_online
from model.world_model import WorldModel


class ApplicationController:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Utwórz handler strumienia
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Utwórz formatter i dodaj go do handlera
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Dodaj handler do loggera
        self.logger.addHandler(handler)
        self.logger.info("Starting script")
        self.should_run = threading.Event()
        self.should_run.set()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.world_controller = WorldController(world_model=WorldModel(), config=self.config)

        asyncio.run(self.run())

    async def run(self) -> None:
        while self.should_run:
            if not internet_online():
                await self.wait_for_internet()
            else:
                config = self.config_manager.config
                self.config_manager.update_config_if_needed(config)
                self.run_villages()

            sleep_time = random.uniform(20, 120)
            await asyncio.sleep(sleep_time)

    def stop(self) -> None:
        self.should_run = False

    async def wait_for_internet(self) -> None:
        self.logger.info("Waiting for internet connection...")
        while not internet_online():
            await asyncio.sleep(1)
        self.logger.info("Internet connection established.")

    def run_villages(self) -> None:
        self.logger.info("Running villages")
        # Implementacja działania skryptu dla wiosek


if __name__ == "__main__":
    app = ApplicationController()
    app.run()
