#!/usr/bin/env python3

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


def get_turn_json(game_id: str, turn: int):
    body = {
        "gameId": game_id,
        "turn": turn,
        "initial": True, # Don't know what this does
    }

    response = requests.post(
        "https://awbw.amarriner.com/api/game/load_replay.php",
        cookies=COOKIE,
        json=body,
    )

    if response.status_code != 200:
        print(f"Got bad response code: {response.status_code}")
        return None
    if "err" in response.json():
        print(response.json()["message"])
        return None

    return response.json()


def get_units_on_turn(game_id: str, turn: int):
    units = {}

    turn_json = get_turn_json(game_id, turn)

    players = list(turn_json["gameState"]["players"].values())
    players = {player["players_id"]: player["users_username"] for player in players}

    for unit_id, data in turn_json["gameState"]["units"].items():
        player = players[data["units_players_id"]]
        unit_name = data["units_name"]

        units[int(unit_id)] = {
            "player": player,
            "unit_name": unit_name,
            "turn_built": None,
        }

    for action in turn_json["actions"]:
        if action["action"] != "Build":
            continue
        # The newly built unit won't already be in the list. Add it
        new_unit = action["newUnit"]
        units[int(new_unit["units_id"])] = {
            "player": players[new_unit["units_players_id"]],
            "unit_name": new_unit["units_name"],
            "turn_built": turn,
        }

    return units


def find_unit_production_days(game_id: str):
    units = {}
    max_turn = 0

    # Get every single unit ever seen
    for turn in range(0, 100):
        sys.stdout.write(f"\rGathering data for turn {turn}...")
        sys.stdout.flush()
        try:
            # DO NOT overwrite old units - they may have their turn filled in
            new_units = get_units_on_turn(game_id, turn)
            units = {**new_units, **units}
        except Exception:
            break
        max_turn = turn

    # Fill in missing data about the enemy units, based on unit ID.
    # Units with ID's less than one from this turn, and that don't have a
    # turn already, must have been made on the previous turn
    turn = 0
    while turn <= max_turn:
        units_built_this_turn = [unit_id for unit_id, data in units.items() if data["turn_built"] == turn]

        if units_built_this_turn:
            unit_from_this_turn = [unit_id for unit_id, data in units.items() if data["turn_built"] == turn][0]
        else:
            # It's probably your turn, and you haven't built yet?
            # If you somehow didn't build for a turn, this script will break
            unit_from_this_turn = sys.maxsize

        for unit_id, data in units.items():
            if unit_id < unit_from_this_turn and data["turn_built"] == None:
                data["turn_built"] = turn - 1

        # Go to MY next turn
        turn += 2

    # Iterate from lowest to highest unit number
    turn = -1
    for unit_id, data in sorted(units.items()):
        unit_name = data["unit_name"]
        player = data["player"]
        turn_built = data["turn_built"]
        if turn < turn_built:
            turn = turn_built
            print(f"=== DAY {turn / 2} ({player}) ===")

        # The -1 turn units are a little glitchy. Don't show
        if turn_built >= 0:
            padding = " " * (12 - len(unit_name))
            print(f"{unit_name}{padding}({unit_id})")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        game_id = sys.argv[1]
    else:
        print("Usage: {} <game-id>".format(sys.argv[1]))
        sys.exit(1)

    COOKIE = get_cookie()

    find_unit_production_days(game_id=game_id)
