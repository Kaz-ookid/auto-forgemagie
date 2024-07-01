import json


# creates a json of every runes with : typeId, nameId, id, iconId; effectId and diceNum
def createRunesBrute(save_file=False, file_name='res/RunesBrute.json'):
    with open("res/Items.json", 'r') as jf:
        json_file = json.load(jf)
    jf.close()

    result = []
    for item in json_file:
        if item["typeId"] == 78:
            rune_json = {}
            key_list = item.keys()
            for key in key_list:
                if key.startswith("typeId") or key.startswith("nameId") or key.startswith("id") or key.startswith(
                        "iconId"):
                    rune_json[key] = item[key]
                if key.startswith("possibleEffects") and len(item[key]) != 0:
                    effect = item[key][0]
                    for effectLine in effect.keys():
                        if effectLine.startswith("effectId") or effectLine.startswith("diceNum"):
                            rune_json[effectLine] = effect[effectLine]
            result.append(rune_json)

    if save_file:
        with open(file_name, 'w') as jf:
            beautified = json.dumps(result, sort_keys=True, indent=4, ensure_ascii=False)
            jf.write(beautified)

        jf.close()

    return result


# creates json of every runes with clear information (text instead of nameId for example)
def createRunesClear(save_file=False, output_file_name='res/RunesClear.json', input_file_name='res/RunesBrute.json'):
    with open(input_file_name, 'r') as jf:
        runes_brute = json.load(jf)
    jf.close()

    with open("res/i18n_fr.json", 'r', encoding='utf8') as jf:
        game_strings = json.load(jf)
    jf.close()

    result = []
    for rune in runes_brute:
        rune_json = {}
        key_list = rune.keys()
        for elem in key_list:
            if elem == "diceNum":
                rune_json["value"] = rune[elem]
            elif elem == "effectId":
                rune_json[elem] = rune[elem]
            elif elem == "iconId":
                rune_json["icon_path"] = "res/items_icons/" + str(rune[elem])
            elif elem == "id":
                rune_json["id"] = rune[elem]
            elif elem == "nameId":
                rune_json["name"] = game_strings["texts"][str(rune[elem])]
            elif elem == "typeId":
                pass
            else:
                print("Rune :[", rune, "] has unexpected attribute : ", elem)
            if "diceNum" not in key_list:
                rune_json["effectId"] = "-1"
                rune_json["value"] = "-1"
        result.append(rune_json)

    if save_file:
        with open(output_file_name, 'w', encoding='utf8') as jf:
            beautified = json.dumps(result, sort_keys=True, indent=4, ensure_ascii=False)
            jf.write(beautified)
        jf.close()

    return result


# creates Effects json template (with a lot to fill in by hands)
# /!\ CHANGE THE NAME OF THE OUTPUT IF REUSING THIS
def createEffects():
    with open("res/ItemTypes.json", 'r') as jf:
        item_types = json.load(jf)
    jf.close()

    with open("res/Items.json", 'r') as jf:
        items = json.load(jf)
    jf.close()

    type_ids = []
    for item_type in item_types:
        if item_type["mimickable"] and item_type["evolutiveTypeId"] == 0 and not type_ids.__contains__(item_type["id"]):
            type_ids.append(item_type["id"])

    effects_ids = []
    already_used_ids = []
    for item in items:
        if type_ids.__contains__(item["typeId"]):
            for effect in item["possibleEffects"]:
                if not already_used_ids.__contains__(effect["effectId"]):
                    already_used_ids.append(effect["effectId"])
                    effect_json = {"id": effect["effectId"], "characteristicName": "", "coefficient": 0}
                    effects_ids.append(effect_json)

    effects_ids_sorted = sorted(effects_ids, key=lambda d: d["id"])
    effects = {}
    for effect in effects_ids_sorted:
        effects[effect["id"]] = effect

    with open('res/Effects.json', 'w', encoding='utf8') as jf:
        beautified = json.dumps(effects, sort_keys=True, indent=4, ensure_ascii=False)
        jf.write(beautified)
    jf.close()

def correct_json_tool():
    with open("res/RunesClear.json", 'r') as jf:
        runes_list = json.load(jf)
    jf.close()
    runes = {}
    for rune in runes_list:
        runes[rune["id"]] = rune
    with open('res/RunesClear.json', 'w', encoding='utf8') as jf:
        beautified = json.dumps(runes, sort_keys=True, indent=4, ensure_ascii=False)
        jf.write(beautified)
    jf.close()

def all_effects_correct_check():
    with open("res/Characteristics.json", 'r') as jf:
        characs_list = json.load(jf)
    jf.close()
    with open("res/Effects.json", 'r') as jf:
        effects_list = json.load(jf)
    jf.close()

    for effect in effects_list.values():

        if not effect["characteristicName"] in characs_list:
            print("An effect has no matching name in Characteristics ID: \nEffect with charateristic name: ", effect["characteristicName"])

        if effect["characteristicName"] != characs_list[effect["characteristicName"]]["name"]:
            print("A characteristic has no matching name and id: \n Charac ID: ", characs_list[effect["characteristicName"]]
                  , "\n Charac name: ", characs_list[effect["characteristicName"]]["name"])
