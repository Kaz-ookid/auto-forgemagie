from pyautogui import *
from AssetsHelper import *

# Fusion Result
CRAFT_CANCELED = -1
CRAFT_IMPOSSIBLE = 0
CRAFT_FAILED = 1
CRAFT_SUCCESS = 2
CRAFT_NEUTRAL = 3
CRAFT_FORBIDDEN = 4

# ResidualPrefix
ADD_RESIDUAL = "+"
SUB_RESIDUAL = "-"
UNCHANGED_RESIDUAL = ""


class Item:

    def add_residual(self, value):
        new_residual = self.residual + value
        if new_residual < 0:
            new_residual = 0
        self.residual = new_residual

    def __init__(self, residual=0, uid=-1, historical=[], stats={}, gid=-1):
        self.residual = residual
        self.uid = uid
        self.gid = gid
        self.historical = historical
        self.stats = stats


class Action:
    def __init__(self, rune_used={}, outcome=CRAFT_CANCELED, residual_prefix=UNCHANGED_RESIDUAL, stats_delta=[]):
        self.rune_used = rune_used
        self.outcome = outcome
        self.residual_prefix = residual_prefix
        self.stats_delta = stats_delta


# Packets IDs
OPEN_WORKBENCH = 3319
CLOSE_TRADE = 6660
ITEM_PLACED = 3145
ITEM_REMOVED = 5821
FUSION_RESULT = 5388
INFORMATION_MESSAGE = 1038
SYSTEM_MESSAGE = 3007
NON_EXISTENT_RECIPE = 269
NOT_ENOUGH_QUANTITY = 57

JobIdWhitelist = [113, 118, 164, 166, 168, 169, 351]


def isWhiteListedJob(msg):
    return JobIdWhitelist.__contains__(msg["skillId"])

def auto_click_on_ok():
    coords = None
    region = (885, 564, 149, 22)
    mouse_x, mouse_y = position()
    while coords is None:
        coords = locateOnScreen('res/OK.png', grayscale=True, region=region)
    x, y = center(coords)
    click(x, y)
    moveTo(mouse_x, mouse_y)


def isRune(msg):
    with open("res/RunesClear.json", 'r') as jf:
        runes = json.load(jf)
    jf.close()
    if str(msg["object"]["objectGID"]) in runes:
        print("---- It's a Rune! ----")

        return True

    print("---- It's not a Rune ----")
    return False


current_rune = {}


def check_rune(msg):
    global current_rune

    with open("res/RunesClear.json", 'r') as jf:
        runes = json.load(jf)
    jf.close()
    current_rune = runes[str(msg["object"]["objectGID"])]


isInWorkbench = None

# keeps a track of the items previously selected
items_dict = {0: Item(uid=0)}
current_item = items_dict[0]


def check_item(msg):
    global current_item
    global items_dict

    with open("res/Effects.json", 'r') as jf:
        effects_dict = json.load(jf)
    jf.close()

    uid = msg["object"]["objectUID"]
    if not any(item_uid == uid for item_uid in items_dict):
        print("----- NEW ITEM -----")
        item = msg["object"]
        stats = {}
        for effect in item["effects"]:  # turning the deboost effects in boost effects with factor -1
            if str(effect["actionId"]) in effects_dict:
                actionId = next(x["id"] for x in effects_dict.values() if (
                        x["characteristicName"] == effects_dict[str(effect["actionId"])]["characteristicName"] and
                        x["coefficient"] == 1))
                stats[actionId] = {"actionId": actionId,
                                   "value": effect["value"] * effects_dict[str(effect["actionId"])]["coefficient"]}

        items_dict[uid] = Item(uid=uid
                               , gid=item["objectGID"]
                               , stats=stats)
    else:
        print("----- NOT NEW ITEM -----")
    print("---- ITEM STATS: ", items_dict[uid].stats)
    current_item = items_dict[uid]


def calculate_residual(stat, old_values, characteristics_list, effects_dict, rune_used):

    # if used rune didnt add all the stats it could (example, use Ra vi and only get +7)
    # , count only 7 residual used and not 10 (by adding the difference in residual)
    if stat["actionId"] == rune_used["effectId"]:
        if stat["value"] > 0:
            if old_values.get(rune_used["effectId"], {"value": 0})["value"] >= -rune_used["value"]:
                return -(
                        characteristics_list[effects_dict[str(rune_used["effectId"])]["characteristicName"]]["weight"]
                        * (rune_used["value"] - stat["value"]))
            else:
                return -(characteristics_list[effects_dict[str(rune_used["effectId"])]["characteristicName"]]
                        ["weight"]*(rune_used["value"] - stat["value"]))
        #elif rune_used["value"] == 0:
        #    return 0

    if old_values[stat["actionId"]]["value"] >= 0 and old_values[stat["actionId"]]["value"] + stat[
        "value"] >= 0:  # if in positive and stays in positive
        print("---- IN POSITIVE ----")
        print("---- generated :",
              characteristics_list[effects_dict[str(stat["actionId"])]["characteristicName"]]["weight"] * stat["value"])
        return characteristics_list[effects_dict[str(stat["actionId"])]["characteristicName"]]["weight"] * stat["value"]
    elif old_values[stat["actionId"]]["value"] < 0 and old_values[stat["actionId"]]["value"] + stat[
        "value"] < 0:  # if in negative and stays in negative
        print("---- IN NEGATIVE ----")
        print("---- generated :", (
                characteristics_list[effects_dict[str(stat["actionId"])]["characteristicName"]]["weight"] * stat[
            "value"]) / 2)
        return (characteristics_list[effects_dict[str(stat["actionId"])]["characteristicName"]]["weight"] * stat[
            "value"]) / 2
    else:
        in_positive = 0
        in_negative = 0
        if old_values[stat["actionId"]]["value"] >= 0:  # if passes by 0
            in_positive = old_values[stat["actionId"]]["value"]
            in_negative = stat["value"] - in_positive
        else:
            in_negative = old_values[stat["actionId"]]["value"] - 1
            in_positive = stat["value"] - in_negative
        print("---- IN BOTH ----")
        print("---- generated :", ((characteristics_list[effects_dict[str(stat["actionId"])]["characteristicName"]][
                                        "weight"] * in_positive) + (
                                           characteristics_list[
                                               effects_dict[str(stat["actionId"])]["characteristicName"]][
                                               "weight"] * in_negative) / 2))
        return ((characteristics_list[effects_dict[str(stat["actionId"])]["characteristicName"]][
                     "weight"] * in_positive) + (
                        characteristics_list[effects_dict[str(stat["actionId"])]["characteristicName"]][
                            "weight"] * in_negative) / 2)


def craft_result(msg):
    with open("res/Effects.json", 'r') as jf:
        effects_dict = json.load(jf)
    jf.close()
    with open("res/Characteristics.json", 'r') as jf:
        characteristics_list = json.load(jf)
    jf.close()

    rune_used = current_rune

    if msg["craftResult"] == CRAFT_CANCELED or msg["craftResult"] == CRAFT_IMPOSSIBLE or msg[
        "craftResult"] == CRAFT_FORBIDDEN:
        current_item.historical.append(
            Action(
                rune_used=rune_used,
                outcome=msg["craftResult"],
            )
        )
        return

    outcome = msg["craftResult"]

    magic_pool_status = msg["magicPoolStatus"]
    residual_prefix = UNCHANGED_RESIDUAL
    if magic_pool_status == 2:
        residual_prefix = ADD_RESIDUAL
    elif magic_pool_status == 3:
        residual_prefix = SUB_RESIDUAL

    old_stats = {stat["actionId"]: stat for stat in current_item.stats.values()}
    current_item.stats = {}
    for stat in msg["objectInfo"]["effects"]:  # turning the deboost effects in boost effects with factor -1
        if str(stat["actionId"]) in effects_dict:
            actionId = next(x["id"] for x in effects_dict.values() if (
                    x["characteristicName"] == effects_dict[str(stat["actionId"])]["characteristicName"] and
                    x["coefficient"] == 1))
            current_item.stats[actionId] = {"actionId": actionId,
                                            "value": stat["value"] * effects_dict[str(stat["actionId"])]["coefficient"]}

    stats_delta = [
        {"actionId": old["actionId"]
            , "value": current_item.stats.get(old["actionId"], {"value": 0})["value"] - old["value"]
         } for old in old_stats.values()]
    if rune_used["effectId"] == 1185:  # if is an orb
        current_item.residual = 0
    else:
        generated_residual = 0
        if residual_prefix == ADD_RESIDUAL or residual_prefix == SUB_RESIDUAL:
            for stat_delta in stats_delta:
                if stat_delta["actionId"] != rune_used["effectId"] or (stat_delta["value"] != rune_used["value"] and stat_delta["value"] != 0):
                    generated_residual -= calculate_residual(stat_delta, old_stats, characteristics_list, effects_dict, rune_used)
            if old_stats.get(rune_used["effectId"], {"value": 0})["value"] >= -rune_used["value"]:
                generated_residual -= (
                        characteristics_list[effects_dict[str(rune_used["effectId"])]["characteristicName"]]["weight"]
                        * rune_used["value"])
            else:
                generated_residual -= (
                                              characteristics_list[
                                                  effects_dict[str(rune_used["effectId"])]["characteristicName"]][
                                                  "weight"]
                                              * rune_used["value"]) / 2
        print("---- RUNE RESIDUAL =", (
                characteristics_list[effects_dict[str(rune_used["effectId"])]["characteristicName"]]["weight"]
                * rune_used["value"]), "----")
        current_item.add_residual(generated_residual)

    current_item.historical.append(
        Action(
            rune_used=rune_used,
            outcome=msg["craftResult"],
            residual_prefix=residual_prefix,
            stats_delta=stats_delta
        )
    )
    print(stats_delta)
    print("---- RESIDUAL: ", current_item.residual)
    print("---- RUNE USED:", rune_used["name"])