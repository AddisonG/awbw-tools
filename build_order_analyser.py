#!/usr/bin/env python3

from typing import Any, Dict, List
from data_objects import Player, Unit
from dataclasses import fields

import argparse
import json
import logging
import os
import requests
import sys
import time


logger = logging.getLogger(__name__)


def get_cookie() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie = json.load(open(script_dir + "/creds.json"))
    if cookie.get("awbw_password") is None:
        raise RuntimeError("Please get a password using F12 dev tools. It should start with '%2A' or '*', followed by 40 hex characters.")

    # Get the PHPSESSID cookie - If we don't have it, 'units' is empty
    response = requests.get(
        "https://awbw.amarriner.com/",
        cookies=cookie,
    )

    for resp_cookie in response.cookies:
        cookie[resp_cookie.name] = resp_cookie.value

    return cookie


class Analyser():

    cookie = None
    game_id: int
    players: Dict[int, Player] = {}
    me: Player

    def __init__(self, game_id: str, debug: bool=False):
        self.game_id = game_id
        self.cookie = get_cookie()
        self.debug = debug

    def get_turn_json(self, turn: int) -> Dict:
        body = {
            "gameId": self.game_id,
            "turn": turn,
            "initial": True,  # Don't know what this does
        }

        response = requests.post(
            "https://awbw.amarriner.com/api/game/load_replay.php",
            cookies=self.cookie,
            json=body,
        )

        if response.status_code != 200:
            raise Exception(f"Got bad response code: {response.status_code}")
        if "err" in response.json():
            raise RuntimeError(response.json()["message"])

        return response.json()


    def get_players(self, players):
        """
        FIXME - actually make a call here, and do it early, not in getunits
        """
        players = list(Player(**data) for data in players.values())

        # We don't support 3+ players
        assert len(players) == 2

        # Find out who is first
        if players[0].players_order < players[1].players_order:
            players[0].first = True
            players[1].first = False
        else:
            players[0].first = False
            players[1].first = True

        # Find out who I am
        if players[0].users_username.lower() == self.cookie.get("awbw_username").lower():
            self.me = players[0]
        else:
            self.me = players[1]

        # Convert to a dict for easy searching
        players = {player.players_id: player for player in players}

        # current_player = players[turn_json["gameState"]["currentTurnPId"]]
        return players


    def get_units_on_turn(self, turn: int) -> Dict[int, Unit]:
        units: Dict[int, Unit] = {}

        turn_json = self.get_turn_json(turn)

        if not self.players:
            self.players = self.get_players(turn_json["gameState"]["players"])

        # Parse units that are visible at turn start
        for unit_id, data in turn_json["gameState"]["units"].items():
            units[int(unit_id)] = Unit(**data, players=self.players)
            if turn == 0:
                # Unit was built before the game began
                units[int(unit_id)].turn_built = -1

        # Parse units that were made visible by actions (move, build, etc)
        for action in turn_json["actions"]:
            if action.get("discovered") and "units" in action["discovered"]:
                for discovered_unit in action["discovered"]["units"]:
                    discovered_unit = Unit(**discovered_unit, players=self.players)
                    units[discovered_unit.units_id] = discovered_unit

            if action["action"] == "Build":
                new_unit = Unit(**action["newUnit"], turn_built=turn, players=self.players)
                units[int(new_unit.units_id)] = new_unit
            elif action["action"] == "Move":
                moving_unit = Unit(**action["unit"], players=self.players)
                units[int(moving_unit.units_id)] = moving_unit

                if not moving_unit.units_x and not moving_unit.units_y:
                    # Unit moved out of vision
                    moving_unit.units_x = action["path"][-1]["x"]
                    moving_unit.units_y = action["path"][-1]["y"]

                    # HACK - this is impossible information to know
                    # Technically cheating, but I already told the site admin
                    # and he doesn't care.
                    moving_unit.extra_distance = action["dist"] - (len(action["path"]) - 1)
            elif action["action"] == "Fire":
                defender = action.get("defender")
                attacker = action.get("attacker")
                if attacker == "?":
                    units[9999999999999] = Unit(units_id=999999999999, units_name="Unknown Artillery", units_players_id=action["copValues"]["attacker"]["playerId"], players=self.players)
                elif attacker["units_id"] in units:
                    units[attacker["units_id"]].units_hit_points = attacker["units_hit_points"]
                if defender["units_id"] in units:
                    units[defender["units_id"]].units_hit_points = defender["units_hit_points"]
            elif action["action"] == "Join":
                joined_unit = Unit(**action["joinedUnit"], players=self.players)
                units[int(joined_unit.units_id)] = joined_unit

                # Set this unit HP to zero - it's kinda dead?
                units[action["joinId"]].units_hit_points = 0
            elif action["action"] == "Unload":
                unloaded_unit = Unit(**action["unloadedUnit"], players=self.players)
                units[int(unloaded_unit.units_id)] = unloaded_unit

                # Glitchy - we know the transport ID, but nothing else! Hahaha
                if action["transportId"] not in units:
                    # DANGER - STUPID MONKEY CODING HERE
                    units[int(action["transportId"])] = Unit(
                        units_id=action["transportId"],
                        units_name="MYSTERY TRANSPORT",
                        units_players_id=unloaded_unit.units_players_id,
                        players=self.players,
                    )

        return units


    def find_unit_production_days(self, only_enemy: bool) -> None:
        all_units: Dict[int, Unit] = {}
        max_turn = 0

        # Get every single unit ever seen
        for turn in range(0, 100):
            sys.stdout.write(f"\rGathering data for day {turn / 2 + 1}...")
            sys.stdout.flush()
            try:
                new_units = self.get_units_on_turn(turn)

                # Update units
                for unit_id, new_unit in new_units.items():
                    new_unit.last_seen_turn = turn
                    if unit_id in all_units:
                        # Preserve turn_built if it already exists
                        # Stops us from forgetting a unit was built on turn zero
                        new_unit.turn_built = all_units[unit_id].turn_built
                    all_units[unit_id] = new_unit
            except RuntimeError as e:
                # Normal "healthy" exception (probably no more turns left)
                print(e)
                break
            except Exception as e:
                logger.exception(e)
                time.sleep(3)
                break
            max_turn = turn

        # Fill in missing data about the enemy units, based on unit ID.
        # Units with ID's less than one from this turn, and that don't have a
        # turn already, must have been made on the previous turn
        turn = -1
        while turn <= max_turn:
            units_built_this_turn = {unit_id: data for unit_id, data in all_units.items() if data.turn_built == turn}

            if units_built_this_turn:
                id_from_this_turn = list(units_built_this_turn.keys())[0]
            elif turn <= 0:
                # Wait until you build a unit - that will be your first turn
                turn += 1
                continue
            else:
                # It's probably your turn, and you haven't built yet?
                # If you somehow didn't build for a turn, this script will break
                id_from_this_turn = 2 ** 64

            for unit_id, unit_data in all_units.items():
                if unit_id < id_from_this_turn and unit_data.turn_built is None:
                    # Should only happen for opponent units - built last turn
                    unit_data.turn_built = turn - 1

            # Go to MY next turn
            turn += 2

        # Group units by turn, for easy display
        units_by_turn: Dict[int, List[Unit]] = {}
        for unit_data in all_units.values():
            if unit_data.turn_built not in units_by_turn:
                units_by_turn[unit_data.turn_built] = []
            units_by_turn[unit_data.turn_built].append(unit_data)

        turn = None
        total_value = {
            "even": 0,
            "odd": 0,
        }
        for turn, units in sorted(units_by_turn.items()):
            turn_type = "odd" if turn % 2 else "even"

            if only_enemy:
                # Only print enemy info
                # FYI - the first turn is turn zero
                if self.me.first and turn_type == "even":
                    continue
                if not self.me.first and turn_type == "odd":
                    continue

            daily_value = sum(unit.units_cost or 0 for unit in units)
            total_value[turn_type] += daily_value

            print(f"\n=== DAY {(turn / 2) + 1} ({units[0].player_name}) ===")
            print(f"Total: ${total_value[turn_type]}, (+${daily_value})")

            for unit in units:
                health = unit.units_hit_points
                status = f"{health}HP" if health else "DEAD"

                # FIXME - janky. this really should factor in current visibility
                if unit.last_seen_turn > max(units_by_turn):
                    last_seen = f"At {unit.units_x}x{unit.units_y}"
                else:
                    last_seen = f"Last seen turn {(unit.last_seen_turn / 2) + 1} at {unit.units_x}x{unit.units_y}"
                if unit.extra_distance:
                    last_seen += f"+{unit.extra_distance}"

                unit_string = f"  {unit.units_name} ({status}) - {last_seen}"
                if self.debug:
                    unit_string += f" - {unit.units_id}"
                print(unit_string)

# TODO - FIND:
# total money spent on repairs (enemy)
# total money spent on units (enemy)
# estimated money earned (entire game)
# estimated troop value, number, and hidden troops


def main():
    parser = argparse.ArgumentParser(description="Find unit production days for a specific game.")
    parser.add_argument(
        "game_id",
        type=str,
        help="The ID of the game."
    )
    parser.add_argument(
        "--only-enemy",
        action="store_true",
        help="If specified, only display enemy data."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show additional debugging information."
    )
    args = parser.parse_args()

    analyser = Analyser(args.game_id, args.debug)
    analyser.find_unit_production_days(only_enemy=args.only_enemy)

if __name__ == "__main__":
    main()
