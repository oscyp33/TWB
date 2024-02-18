import collections
import json
import logging
import os
import sys
from pathlib import Path
from typing import OrderedDict

CONFIG_FILE_NAME = "config.json"
CONFIG_BAK = "config.bak"
TEMPLATE_FILE_NAME = "config.example.json"

ROOT_DIRECTORY = Path(os.path.dirname(__file__)).parent
CONFIG_PATH = Path(os.path.join(ROOT_DIRECTORY, CONFIG_FILE_NAME))


class ConfigManager:
    def __init__(self):
        self.logging = logging.getLogger(__name__)
        self.config_file = CONFIG_FILE_NAME
        self.config = self.config()

    def load_config(self):
        try:
            with open(self.config_file, "r") as f:
                return json.load(f, object_pairs_hook=collections.OrderedDict)
        except FileNotFoundError:
            print("Config file not found.")
            return None
        except json.JSONDecodeError:
            print("Invalid JSON format in config file.")
            return None

    def load_config_file(self, config_file_name: str):
        file_path = Path(os.path.join(ROOT_DIRECTORY, config_file_name))
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f, object_pairs_hook=collections.OrderedDict)
        return None

    def get_value(self, section, parameter, default=None):
        if self.config and section in self.config and parameter in self.config[section]:
            return self.config[section][parameter]
        return default

    def set_value(self, section, parameter, value):
        if self.config:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][parameter] = value

    def save_config(self):
        if self.config:
            try:
                with open(self.config_file, "w") as f:
                    json.dump(self.config, f, indent=4)
                print("Config file saved successfully.")
            except:
                print("Failed to save config file.")

    def config(self) -> OrderedDict:
        template = self.load_config_file(TEMPLATE_FILE_NAME)
        if not os.path.exists(CONFIG_PATH):
            if self.manual_config():
                return self.config()
            else:
                print("Unable to start without a valid config file")
                sys.exit(1)
        config = self.load_config_file(CONFIG_FILE_NAME)
        if template and config["build"]["version"] != template["build"]["version"]:
            print(
                "Outdated config file found, merging (old copy saved as config.bak)\n"
                "Remove config.example.json to disable this behaviour"
            )
            self.backup_config_file(config)
            config = self.merge_configs(config, template)
            self.save_config_file(config, CONFIG_FILE_NAME)
            print("Deployed new configuration file")
        return config

    def manual_config(self):
        logging.info(
            "Hello and welcome, it looks like you don't have a config file (yet)"
        )
        if not os.path.exists(TEMPLATE_FILE_NAME):
            logging.error(
                "Oh no, config.example.json and config.json do not exist. You broke something didn't you?"
            )
            return False
        logging.info(
            "Please enter the current (logged-in) URL of the world you are playing on (or q to exit)"
        )
        input_url = input("URL: ")
        if input_url.strip() == "q":
            return False
        server = input_url.split("://")[1].split("/")[0]
        game_endpoint = input_url.split("?")[0]
        sub_parts = server.split(".")[0]
        logging.info("Game endpoint: %s" % game_endpoint)
        logging.info("World: %s" % sub_parts.upper())
        check = input("Does this look correct? [nY]")
        if "y" in check.lower():
            browser_ua = input(
                "Enter your browser user agent "
                "(to lower detection rates). Just google what is my user agent> "
            )
            if browser_ua and len(browser_ua) < 10:
                logging.error(
                    "It should start with Chrome, Firefox or something. Please try again"
                )
                return self.manual_config()
            browser_ua = browser_ua.strip()
            disclaimer = """
            Read carefully: Please note the use of this bot can cause bans, kicks, annoyances and other stuff.
            I do my best to make the bot as undetectable as possible but most issues / bans are config related.
            Make sure you keep your bot sleeps at a reasonable numbers and please don't blame me if your account gets banned ;) 
            PS. make sure to regularly (1-2 per day) logout/login using the browser session and supply the new cookie string. 
            Using a single session for 24h straight will probably result in a ban
            """
            self.logging.info(disclaimer)
            final_check = input(
                "Do you understand this and still wish to continue, please type: yes and press enter> "
            )
            if "yes" not in final_check.lower():
                logging.info("Goodbye :)")
                sys.exit(0)
            root_directory = os.path.dirname(__file__)
            with open(
                os.path.join(root_directory, TEMPLATE_FILE_NAME), "r"
            ) as template_file:
                template = json.load(
                    template_file, object_pairs_hook=collections.OrderedDict
                )
                template["server"]["endpoint"] = game_endpoint
                template["server"]["server"] = sub_parts.lower()
                template["bot"]["user_agent"] = browser_ua
                with open(os.path.join(root_directory, CONFIG_FILE_NAME), "w") as newcf:
                    json.dump(template, newcf, indent=2, sort_keys=False)
                    print("Deployed new configuration file")
                    return True
        print("Make sure your url starts with https:// and contains the game.php? part")
        return self.manual_config()

    def merge_configs(self, old_config, new_config):
        to_ignore = ["villages", "build"]
        for section in old_config:
            if section not in to_ignore:
                for entry in old_config[section]:
                    if entry in new_config[section]:
                        new_config[section][entry] = old_config[section][entry]
        villages = collections.OrderedDict()
        for v in old_config["villages"]:
            nc = new_config["village_template"]
            vdata = old_config["villages"][v]
            for entry in nc:
                if entry not in vdata:
                    vdata[entry] = nc[entry]
            villages[v] = vdata
        new_config["villages"] = villages
        return new_config

    def backup_config_file(self, config):
        root_directory = os.path.dirname(__file__)
        with open(os.path.join(root_directory, CONFIG_BAK), "w") as backup:
            json.dump(config, backup, indent=2, sort_keys=False)

    def save_config_file(self, config, filename):
        root_directory = os.path.dirname(__file__)
        with open(os.path.join(root_directory, filename), "w") as newcf:
            json.dump(config, newcf, indent=2, sort_keys=False)

    def add_village(self, vid, template=None):
        original = self.config
        with open(os.path.join(ROOT_DIRECTORY, CONFIG_BAK), "w") as backup:
            json.dump(original, backup, indent=2, sort_keys=False)
        if not template and "village_template" not in original:
            print("Village entry %s could not be added to the config file!" % vid)
            return
        original["villages"][vid] = (
            template if template else original["village_template"]
        )
        with open(os.path.join(ROOT_DIRECTORY, CONFIG_FILE_NAME), "w") as newcf:
            json.dump(original, newcf, indent=2, sort_keys=False)
            print("Deployed new configuration file")

    def update_config_if_needed(self, new_config):
        if self.config != new_config:
            self.save_config_file(new_config, CONFIG_FILE_NAME)
            self.config = new_config
            print("Config file updated.")

    def deploy_new_configuration(self, config):
        try:
            with open(CONFIG_PATH, "w") as new_config_file:
                json.dump(config, new_config_file, indent=2, sort_keys=False)
            print("New configuration deployed successfully.")
        except Exception as e:
            print(f"Failed to deploy new configuration: {e}")


if __name__ == "__main__":
    print("This is a module, not a script")
    config = ConfigManager()
    print("Done")
