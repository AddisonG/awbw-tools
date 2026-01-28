from dataclasses import dataclass, fields
from typing import Any, Dict, Optional


@dataclass
class Player:
    users_username: str
    users_id: int
    players_id: int
    players_team: Optional[str]
    players_countries_id: Optional[int]
    players_eliminated: Optional[str]
    players_co_id: Optional[int]
    co_name: Optional[str]
    co_image_path: Optional[str]
    co_grayscale_image_path: Optional[str]
    co_max_power: Optional[int]
    co_max_spower: Optional[int]
    players_co_power: Optional[int]
    players_co_power_on: Optional[str]
    players_co_max_power: Optional[int]
    players_co_max_spower: Optional[int]
    players_co_image: Optional[str]
    players_funds: Optional[int]
    countries_code: Optional[str]
    countries_name: Optional[str]
    numProperties: Optional[int]
    cities: Optional[int]
    labs: Optional[int]
    towers: Optional[int]
    other_buildings: Optional[int]
    players_turn_clock: Optional[int]
    players_turn_start: Optional[str]
    players_order: int

    players_income: Optional[int] = None
    first: Optional[bool] = None

    def __repr__(self) -> str:
        return f"<Player {self.users_username} ({self.players_id})>"


@dataclass
class Unit:
    units_id: int
    units_games_id: int
    units_players_id: int
    units_name: str
    units_movement_points: int
    units_vision: int
    units_fuel: int
    units_fuel_per_turn: int
    units_sub_dive: str
    units_ammo: int
    units_short_range: int
    units_long_range: int
    units_second_weapon: str
    units_cost: int
    units_movement_type: str
    units_x: int
    units_y: int
    units_moved: int
    units_capture: int
    units_fired: int
    units_hit_points: int  # Probably breaks for Sonja. Probably everything breaks lol
    units_cargo1_units_id: int
    units_cargo2_units_id: int
    units_carried: str
    countries_code: str

    # Sometimes these are not present?
    units_symbol: Optional[str] = None
    generic_id: Optional[int] = None

    # Manually added attrs
    player_name: Optional[str] = None
    turn_built: Optional[int] = None
    extra_distance: Optional[int] = None
    last_seen_turn: Optional[int] = None

    def __init__(self, players: Dict[int, Player], **kwargs: Any) -> None:
        # Get the field names from the dataclass
        valid_fields = {f.name for f in fields(self.__class__)}
        # Set all valid fields to None initially
        for field in valid_fields:
            setattr(self, field, None)

        # Update with provided kwargs, filtering only valid fields
        for key, value in kwargs.items():
            if key in valid_fields:
                setattr(self, key, value)

        # Set player name based on ID - FIXME this is such a dumb hack
        self.player_name = players[self.units_players_id].users_username

        self.__fix_unit_cost__()

    def __fix_unit_cost__(self) -> None:
        """
        If a unit passes across the screen, but does not finish movement in
        vision, many of these will be empty, causing issues. Most concerning is
        `units_cost`, which I have jankily hardcoded to be slightly fixed for
        common use cases.
        """
        lookup = {
            "black boat": 7500,
            "piperunner": 20000,
            "black bomb": 25000,
            "infantry": 1000,
            "mech": 3000,
            "md.tank": 16000,
            "tank": 7000,
            "recon": 4000,
            "apc": 5000,
            "artillery": 6000,
            "rocket": 15000,
            "anti-air": 8000,
            "missile": 12000,
            "fighter": 20000,
            "bomber": 22000,
            "b-copter": 9000,
            "t-copter": 5000,
            "battleship": 28000,
            "cruiser": 18000,
            "lander": 12000,
            "sub": 20000,
            "neotank": 22000,
            "mega tank": 28000,
            "carrier": 30000,
            "stealth": 24000,
            # FIXME use that actual lookup that old mate has in the gamestate json (generic_units)
        }

        if not self.units_cost and self.units_name:
            self.units_cost = lookup.get(self.units_name.lower(), 0)

    def __repr__(self) -> str:
        return f"<Unit {self.units_name} ({self.units_id}) {self.player_name} turn {self.turn_built}>"
