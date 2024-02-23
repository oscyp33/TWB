import re
from typing import List, Dict, Optional, Tuple

from bs4 import BeautifulSoup


class Point:
    """Represents a point with x and y coordinates."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class Farm:
    """Represents farm population."""

    def __init__(self, population_str: str):
        """
        Initializes a Farm object.

        Args:
            population_str (str): The string representation of population.
                Format: 'current/maximum'.
        """
        current, maximum = map(int, population_str.split("/"))
        self.current = current
        self.maximum = maximum


class Storage:
    """Represents storage resources (wood, stone, iron)."""

    def __init__(self, resources: str, capacity: str):
        """
        Initializes a Storage object.

        Args:
            resources (str): The string representation of resources.
                Format: 'wood stone iron'.
        """
        resources = resources.replace(".", "")
        self.wood, self.stone, self.iron = map(int, resources.split())


class Village:
    """Represents a village with its name, coordinates, and continent."""

    def __init__(
        self,
        village_id: str,
        village_name: str,
        coordinates: Point,
        continent: str,
        points: str,
        storage: Storage,
        farm: Farm,
    ):
        """
        Initializes a Village object.

        Args:
            village_id (str): The ID of the village.
            village_str (str): The string representation of the village.

        Raises:
            ValueError: If the village string format is invalid.
        """
        self.village_id = village_id
        self.village_name = village_name
        self.coordinates = coordinates
        self.continent = continent
        self.points = points
        self.storage = storage
        self.farm = farm

    def parse_coordinates(self, cords: str) -> Point:
        """
        Parse the coordinates string and return a Point object.

        Args:
            cords (str): The string representation of coordinates.

        Returns:
            Point: The Point object with parsed coordinates.
        """
        x, y = map(int, cords.strip("()").split("|"))
        return Point(x, y)


class OverviewPage:
    """Represents the overview page with village data and world options."""

    def __init__(self, wrapper):
        """
        Initializes an OverviewPage object.

        Args:
            wrapper: The wrapper object for making HTTP requests.
        """
        self.flags: bool = Optional[bool]
        self.knight: bool = Optional[bool]
        self.boosters: bool = Optional[bool]
        self.quests: bool = Optional[bool]
        self.wrapper = wrapper
        self.result_get = self.wrapper.get_url("game.php?screen=overview_villages")
        self.soup = BeautifulSoup(self.result_get.text, "html.parser")
        self.header_info = self.soup.find("table", {"id": "header_info"})
        self.production_table = self.soup.find("table", {"id": "production_table"})
        self.production_table_data: List[Dict[str, any]] = []
        self.parse_production_table()
        self.parse_header_info()

    def parse_production_table(self):
        """Parse the production table to extract village data."""
        if self.production_table:
            rows = self.production_table.find_all("tr")
            for row in rows:
                if row.find_all("td"):
                    cells = row.find_all("td")
                    village_id = cells[0].contents[1].attrs["data-id"]
                    name, coordinates, continent = self._extract_name_cords_continent(
                        cells[0].text.strip()
                    )
                    points = cells[1].text.strip()
                    resources = cells[2].text.strip()
                    storage_capacity = cells[3].text.strip()

                    storage = Storage(resources, storage_capacity)
                    farm = Farm(cells[4].text.strip())
                    village = Village(
                        village_id, name, coordinates, continent, points, storage, farm
                    )
                    self.production_table_data.append(
                        {
                            "id": village_id,
                            "village": village,
                            "points": points,
                            "storage_capacity": storage_capacity,
                            "storage": storage,
                            "farm": farm,
                        }
                    )

    def parse_header_info(self) -> None:
        """Parse header information to get world options."""
        text = self.result_get.text

        self.flags = "screen=flags" in text
        self.knight = "screen=statue" in text
        self.boosters = "screen=inventory" in text
        self.quests = "Quests.setQuestData" in text

    @staticmethod
    def _extract_name_cords_continent(cell_value: str) -> Tuple[str, Point, str]:
        """Extract name, coordinates and continent from cell value."""
        match = re.match(r"(.+)\s\((\d+)\|(\d+)\)\s(.+)", cell_value)
        if match:
            name = match.group(1)
            coordinates = Point(int(match.group(2)), int(match.group(3)))
            continent = match.group(4)
            return name, coordinates, continent
        else:
            raise ValueError("Invalid village string format")
