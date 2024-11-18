#!/usr/bin/env python3

from typing import Any, Dict
from data_objects import Player, Unit
from dataclasses import fields

import requests
import json
import sys
import os


def get_cookie():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie = json.load(open(script_dir + "/creds.json"))
    if cookie["awbw_password"] is None:
        raise RuntimeError("Please get a password using F12 dev tools. It should start with '%2A' or '*', followed by 40 hex characters.")

    # Get the PHPSESSID cookie - If we don't have it, 'units' is empty
    response = requests.get(
        "https://awbw.amarriner.com/",
        cookies=cookie,
    )

    for resp_cookie in response.cookies:
        cookie[resp_cookie.name] = resp_cookie.value

    return cookie


def get_turn_json(game_id: str, turn: int) -> Dict:
    body = {
        "gameId": game_id,
        "turn": turn,
        "initial": True,  # Don't know what this does
    }

    response = requests.post(
        "https://awbw.amarriner.com/api/game/load_replay.php",
        cookies=COOKIE,
        json=body,
    )

    if response.status_code != 200:
        raise Exception(f"Got bad response code: {response.status_code}")
    if "err" in response.json():
        raise Exception(response.json()["message"])

    return response.json()


def get_units_on_turn(game_id: str, turn: int) -> Dict[int, Unit]:
    units: Dict[int, Unit] = {}

    turn_json = get_turn_json(game_id, turn)

    players = list(Player(**data) for data in turn_json["gameState"]["players"].values())

    # We don't support 3+ players
    assert len(players) == 2

    players = {player.players_id: player for player in players}
    # current_player = players[turn_json["gameState"]["currentTurnPId"]]

    # Parse units that are visible at turn start
    for unit_id, data in turn_json["gameState"]["units"].items():
        units[int(unit_id)] = Unit(**data, players=players)
        if turn == 0:
            # Unit was built before the game began
            units[int(unit_id)].turn_built = -1

    # Parse units that were made visible by actions (move, build, etc)
    for action in turn_json["actions"]:
        if action.get("discovered") and "units" in action["discovered"]:
            for discovered_unit in action["discovered"]["units"]:
                discovered_unit = Unit(**discovered_unit, players=players)
                units[discovered_unit.units_id] = discovered_unit

        if action["action"] == "Build":
            new_unit = Unit(**action["newUnit"], turn_built=turn, players=players)
            units[int(new_unit.units_id)] = new_unit
        elif action["action"] == "Move":
            moving_unit = Unit(**action["unit"], players=players)
            units[int(moving_unit.units_id)] = moving_unit
        elif action["action"] == "Fire":
            # FIXME - Add hidden artillery?
            defender = action.get("defender")
            attacker = action.get("attacker")
            if attacker["units_id"] in units:
                units[attacker["units_id"]].units_hit_points = attacker["units_hit_points"]
            if defender["units_id"] in units:
                units[defender["units_id"]].units_hit_points = defender["units_hit_points"]
        elif action["action"] == "Unload":
            unloaded_unit = Unit(**action["unloadedUnit"], players=players)
            units[int(unloaded_unit.units_id)] = unloaded_unit

            # Glitchy - we know the transport ID, but nothing else! Hahaha
            if action["transportId"] not in units:
                # DANGER - STUPID MONKEY CODING HERE
                units[int(action["transportId"])] = Unit(
                    units_id=action["transportId"],
                    units_name="MYSTERY TRANSPORT",
                    units_players_id=unloaded_unit.units_players_id,
                    players=players,
                )

    return units


def find_unit_production_days(game_id: str) -> None:
    units: Dict[int, Unit] = {}
    max_turn = 0

    # Get every single unit ever seen
    for turn in range(0, 100):
        sys.stdout.write(f"\rGathering data for day {turn / 2 + 1}...")
        sys.stdout.flush()
        try:
            new_units = get_units_on_turn(game_id, turn)

            # Update units
            for unit_id, new_unit in new_units.items():
                if unit_id in units:
                    # Preserve turn_built if it already exists
                    # Stops us from forgetting a unit was built on turn zero
                    new_unit.turn_built = units[unit_id].turn_built
                units[unit_id] = new_unit
        except Exception as e:
            print(e)
            break
        max_turn = turn

    # Fill in missing data about the enemy units, based on unit ID.
    # Units with ID's less than one from this turn, and that don't have a
    # turn already, must have been made on the previous turn
    turn = -1
    while turn <= max_turn:
        units_built_this_turn = {unit_id: data for unit_id, data in units.items() if data.turn_built == turn}

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

        for unit_id, unit_data in units.items():
            if unit_id < id_from_this_turn and unit_data.turn_built is None:
                # if data["player"] == units_built_this_turn[id_from_this_turn]["player"]:
                #     # Should only happen for your own pre-deployed units
                #     data.turn_built = turn - 2
                # else:
                # Should only happen for opponent units - built last turn
                unit_data.turn_built = turn - 1

        # Go to MY next turn
        turn += 2

    units_by_turn = {}
    for unit_data in units.values():
        if unit_data.turn_built not in units_by_turn:
            units_by_turn[unit_data.turn_built] = []
        units_by_turn[unit_data.turn_built].append(unit_data)

    # Iterate from lowest to highest unit number
    turn = None
    for unit_id, unit_data in sorted(units.items()):
        turn_built = unit_data.turn_built
        if turn != turn_built:
            turn = turn_built
            print(f"\n=== DAY {(turn / 2) + 1} ({unit_data.player_name}) ===")

        health = unit_data.units_hit_points
        status = f"{health}HP" if health else "DEAD"

        print(f"{unit_data.units_name} ({status}) - {unit_id}")

# TODO - FIND:
# total money spent on repairs (enemy)
# total money spent on units (enemy)
# estimated money earned (entire game)
# estimated troop value, number, and hidden troops

if __name__ == "__main__":
    if len(sys.argv) == 0 or "-" in sys.argv[1]:
        print("Usage: {} <game-id>".format(sys.argv[0]))
        sys.exit(1)

    COOKIE = get_cookie()

    game_id = sys.argv[1]
    find_unit_production_days(game_id=game_id)
