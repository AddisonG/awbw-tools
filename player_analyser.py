#!/usr/bin/env python3

from enum import Enum
import json
import html
import re
import os
import sys
import requests

# Analyse user's opening strategy


class GameType(Enum):
    ALL = "all"
    STANDARD = "std"
    FOG = "fog"
    HIGH_FUNDS = "hf"


def get_user_replays(username: str, game_type: GameType = GameType.ALL):
    response = requests.get(
        f"https://awbw.amarriner.com/gamescompleted.php?start=1&username={username}&type={game_type.value}",
        cookies=cookie,
    )
    content = html.unescape(response.text)

    pattern = re.compile(r'2030.php\?games_id=(\d+)&ndx=0')
    game_ids = []
    for game_id in re.findall(pattern, content):
        game_ids.append(game_id)

    return game_ids


def get_map_replays(map_id: str, game_type: GameType = GameType.ALL):
    response = requests.get(
        f"https://awbw.amarriner.com/gamescompleted.php?maps_id={map_id}",
        cookies=cookie,
    )
    content = html.unescape(response.text)

    pattern = re.compile(r'2030.php\?games_id=(\d+)&ndx=0')
    game_ids = []
    for game_id in re.findall(pattern, content):
        game_ids.append(game_id)

    return game_ids


def analyse_game(game_id: str, player: str, turns: int):
    # Get the first turn, so we can find info like player name, CO, etc.
    body = {
        "gameId": game_id,
        "turn": 0,
    }

    response = requests.post(
        "https://awbw.amarriner.com/api/game/load_replay.php",
        cookies=cookie,
        json=body,
    )
    try:
        players = list(response.json()["gameState"]["players"].values())
    except Exception:
        return {}

    if player == "0" or player == players[0]["users_username"]:
        player_num = 0
    else:
        player_num = 1
    player_co = players[player_num]["co_name"]

    print(f"ANALYSING GAME {game_id}. {player} playing as {player_co}")

    all_units = {}
    unit_count = 0
    for turn in range(0 + player_num, (turns * 2) + player_num, 2):
        units, captures, income = analyse_turn(game_id, turn)
        if units is None:
            if turn <= 1:
                print("No game info")
                return {}
            break
        for unit, num in units.items():
            if unit == "Infantry":
                continue
            unit_count += num
            if unit not in all_units:
                all_units[unit] = num
            else:
                all_units[unit] += num

    unit_ratios = {}
    for key, val in all_units.items():
        unit_ratios[key] = str(round(val / unit_count * 100, 2)) + "%"

    print(f"=={turns}-TURN RATIOS==")
    print(unit_ratios or "No non-infantry units produced")
    print()

    return unit_ratios


def analyse_turn(game_id: str, turn: int):
    body = {
        "gameId": game_id,
        "turn": turn,
    }

    response = requests.post(
        "https://awbw.amarriner.com/api/game/load_replay.php",
        cookies=cookie,
        json=body,
    )

    if response.status_code != 200:
        return None
    if "err" in response.json():
        print(response.json()["message"])
        return None

    units_built, captures = analyse_actions(response.json())

    # Funds leftover from LAST turn
    pid = str(response.json()["gameState"]["currentTurnPId"])
    player_info = response.json()["gameState"]["players"][pid]
    funds = player_info["players_funds"]
    income = player_info["players_income"]
    print(f"Day {turn//2}. ${funds - income} leftover + ${income}. Captures: {captures}.")

    return units_built, captures, income

def analyse_actions(response):
    units_built = {}
    captures = 0

    for action in response["actions"]:
        action_type = action["action"]
        # BUILD
        if action_type == "Build":
            unit_name = action["newUnit"]["units_name"]
            if unit_name in units_built:
                units_built[unit_name] += 1
            else:
                units_built[unit_name] = 1
        # CAPTURE
        if action_type == "Capt":
            if action["buildingInfo"]["buildings_capture"] == 20:
                captures += 1

    return units_built, captures


def debug_action(action):
    action_type = action["action"]

    if action_type == "Build":
        unit_name = action["newUnit"]["units_name"]
        print(f"Build {unit_name}.")
    elif action_type == "Move":
        unit_name = action["unit"]["units_name"]
        print(f"Move {unit_name}.")


def setup():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie = json.load(open(script_dir + "/creds.json"))
    if cookie["awbw_password"] is None:
        print("Please get a password using F12 dev tools. It should start with '%2A' or '*', followed by 40 hex characters.")
        exit(1)

    return cookie


if __name__ == "__main__":
    cookie = setup()
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--help", "-h"):
            print("Usage: {} [username]".format(sys.argv[0]))
            sys.exit(1)
        player_name = sys.argv[1]
    else:
        player_name = cookie["awbw_username"]

    # TODO - arg to change mode, or turn numbers
    replays = get_user_replays(player_name, GameType.FOG)
    if not replays:
        print("Could not find any games to analyse")
    try:
        for replay in replays:
            analyse_game(replay, player_name, 12)
    except Exception as e:
        print("Exception. Exiting.")
        print(e)
