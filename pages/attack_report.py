from bs4 import BeautifulSoup
import json
from datetime import datetime

from core.extractors import Extractor


class AttackReportPage:
    def __init__(self):
        self.last_reports = {}
        self.logger = None  # Dodaj logger, jeśli jest potrzebny
        self.game_state = None  # Dodaj stan gry, jeśli jest potrzebny

    def attack_report(self, report, report_id):
        extra = {}
        losses = {}

        soup = BeautifulSoup(report, 'html.parser')

        extra.update(self._extract_attack_info(soup))
        extra.update(self._extract_defense_info(soup))
        extra.update(self._extract_results(soup))
        extra.update(self._extract_scout_info(soup))

        attack_type = "scout" if self._is_scout(soup) else "attack"
        res = self.put(
            report_id, attack_type, extra.get("from_village"), extra.get("to_village"), data=extra, losses=losses
        )
        self.last_reports[report_id] = res
        return True

    def _extract_attack_info(self, soup):
        extra = {}
        attacker = soup.find(id="attack_info_att")
        if attacker:
            from_player = attacker["data-player"]
            from_village = attacker["data-id"]
            units = attacker.find("table", id="attack_info_att_units")
            if units:
                sent_units = units.find_all("tr")
                extra["units_sent"] = self.re_unit(
                    Extractor.units_in_total(sent_units[0])
                )
                if len(sent_units) == 2:
                    extra["units_losses"] = self.re_unit(
                        Extractor.units_in_total(sent_units[1])
                    )
                    if from_player == self.game_state["player"]["id"]:
                        losses = extra["units_losses"]
        return extra

    def _extract_defense_info(self, soup):
        extra = {}
        defender = soup.find(id="attack_info_def")
        if defender:
            to_player = defender["data-player"]
            to_village = defender["data-id"]
            units = defender.find("table", id="attack_info_def_units")
            if units:
                def_units = units.find_all("tr")
                extra["defence_units"] = self.re_unit(
                    Extractor.units_in_total(def_units[0])
                )
                if len(def_units) == 2:
                    extra["defence_losses"] = self.re_unit(
                        Extractor.units_in_total(def_units[1])
                    )
                    if to_player == self.game_state["player"]["id"]:
                        losses = extra["defence_losses"]
        return extra

    def _extract_results(self, soup):
        extra = {}
        results = soup.find(id="attack_results")
        if results:
            loot = {}
            for loot_entry in results.find_all(class_="icon header"):
                resource = loot_entry["class"][2]
                amount = loot_entry.next_sibling.strip()
                loot[resource] = amount
            extra["loot"] = loot
            self.logger.info("attack report %s -> %s" % (from_village, to_village))
        return extra

    def _extract_scout_info(self, soup):
        extra = {}
        scout_results = soup.find(id="attack_spy_resources")
        if scout_results:
            self.logger.info("scout report %s -> %s" % (from_village, to_village))
            scout_buildings = soup.find(id="attack_spy_building_data")
            if scout_buildings:
                raw = scout_buildings["value"].replace("&quot;", '"')
                extra["buildings"] = self.re_building(json.loads(raw))
            found_res = {}
            for loot_entry in scout_results.find_all(class_="icon header"):
                resource = loot_entry["class"][2]
                amount = loot_entry.next_sibling.strip()
                found_res[resource] = amount
            extra["resources"] = found_res
            units_away = soup.find(id="attack_spy_away")
            if units_away:
                data_away = self.re_unit(Extractor.units_in_total(units_away))
                extra["units_away"] = data_away
        return extra

    def _is_scout(self, soup):
        return bool(soup.find(id="attack_spy_resources"))
