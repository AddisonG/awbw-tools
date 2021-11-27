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
    body = {
        "gameId": game_id,
        "turn": 0,
        "initial": True,
    }

    response = requests.post(
        "https://awbw.amarriner.com/api/game/load_replay.php",
        cookies=cookie,
        json=body,
    )
    players = list(response.json()["gameState"]["players"].values())

    if player == 0 or player == players[0]["users_username"]:
        player_num = 0
    else:
        player_num = 1
    player_co = players[player_num]["co_name"]

    print(f"\nANALYSING GAME {game_id}. {player} playing as {player_co}")

    all_units = {}
    unit_count = 0
    for turn in range(0 + player_num, (turns * 2) + player_num, 2):
        units = analyse_turn(game_id, turn)
        if units is None:
            if turn <= 1:
                print("No game info")
                return {}
            break
        # print(units)
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
    print(unit_ratios)

    return unit_ratios


def analyse_turn(game_id: str, turn: int):
    body = {
        "gameId": game_id,
        "turn": turn,
        "initial": True, # What does this do?
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

    # players = list(response.json()["gameState"]["players"].values())

    # player_1 = "Player 1 - " + players[0]["users_username"] + " (" + players[0]["co_name"] + ")."
    # player_2 = "Player 2 - " + players[1]["users_username"] + " (" + players[1]["co_name"] + ")."

    # print("Day: " + str(response.json()["day"]) + ". " + (player_2 if turn % 2 else player_1))

    # players_income
    # players_funds

    units_built = {}
    for action in response.json()["actions"]:
        # print_action(action)

        action_type = action["action"]
        if action_type == "Build":
            unit_name = action["newUnit"]["units_name"]
            if unit_name in units_built:
                units_built[unit_name] += 1
            else:
                units_built[unit_name] = 1

    return units_built


def print_action(action):
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

cookie = setup()
if len(sys.argv) > 1:
    player_name = sys.argv[1]
else:
    player_name = cookie["awbw_username"]

# replays = get_user_replays(player_name, GameType.FOG)
# try:
#     for replay in replays:
#         analyse_game(replay, player_name, 12)
# except Exception:
#     print("Exception. Exiting.")


replays = get_map_replays(79404, GameType.FOG)
try:
    for replay in replays:
        analyse_game(replay, 0, 8)
except Exception:
    print("Exception. Exiting.")
