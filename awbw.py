#!/usr/bin/env python3

from enum import Enum
import json
import html
import re
import requests

# Analyse user's opening strategy

class GameType(Enum):
    ALL = "std"
    STANDARD = "std"
    FOG = "fog"
    HIGH_FUNDS = "hf"

cookie = json.load(open("creds.json"))
if cookie["awbw_password"] is None:
    print("Please get a password using F12 dev tools. It should look like '%2ABCD1234'.")
    exit(1)

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


def analyse_game(game_id: str, player: str):

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

    if player == players[0]["users_username"]:
        player_num = 0
    else:
        player_num = 1
    player_co = players[player_num]["co_name"]

    print(f"\nANALYSING GAME {game_id}. {player} playing as {player_co}")

    all_units = {}
    unit_count = 0
    for turn in range(0 + player_num, 20 + player_num, 2):
        units = analyse_turn(game_id, turn)
        if units is None:
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

    print("==10-TURN RATIOS==")
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

player_name = "corr0s1ve"
replays = get_user_replays(player_name, GameType.FOG)

for replay in replays:
    analyse_game(replay, player_name)
