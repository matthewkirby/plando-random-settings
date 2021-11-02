import os
import sys
import datetime
import json
import random
import conditionals as conds
from version import version_hash_1, version_hash_2
sys.path.append("randomizer")
from randomizer.SettingsList import get_settings_from_tab, get_setting_info
from randomizer.StartingItems import inventory, songs, equipment
from randomizer.Spoiler import HASH_ICONS


def load_weights_file(weights_fname):
    """ Given a weights filename, open it up. If the file does not exist, make it with even weights """
    fpath = os.path.join("weights", weights_fname)
    if os.path.isfile(fpath):
        with open(fpath) as fin:
            datain = json.load(fin)

    weight_options = datain["options"] if "options" in datain else None
    weight_dict = datain["weights"]

    return weight_options, weight_dict


def generate_balanced_weights(fname="default_weights.json"):
    """ Generate a file with even weights for each setting. """
    settings_to_randomize = list(get_settings_from_tab("main_tab"))[1:] + \
                list(get_settings_from_tab("detailed_tab")) + \
                list(get_settings_from_tab("other_tab")) + \
                list(get_settings_from_tab("starting_tab"))

    exclude_from_weights = ["bridge_tokens", "ganon_bosskey_tokens", "triforce_goal_per_world", "disabled_locations",
                            "allowed_tricks", "starting_equipment", "starting_items", "starting_songs"]
    weight_dict = {}
    for name in settings_to_randomize:
        if name not in exclude_from_weights:
            opts = list(get_setting_info(name).choices.keys())
            optsdict = {o: 100./len(opts) for o in opts}
            weight_dict[name] = optsdict

    if fname is not None:
        with open(fname, 'w') as fp:
            json.dump(weight_dict, fp, indent=4)
    
    return weight_dict


def geometric_weights(N, startat=0, rtype="list"):
    """ Compute weights according to a geometric distribution """
    if rtype == "list":
        return [50.0/2**i for i in range(N)]
    elif rtype == "dict":
        return {str(startat+i): 50.0/2**i for i in range(N)}


def draw_starting_item_pool(random_settings, start_with):
    """ Select starting items, songs, and equipment. """
    random_settings["starting_items"] = draw_choices_from_pool(inventory)
    random_settings["starting_songs"] = draw_choices_from_pool(songs)
    random_settings["starting_equipment"] = draw_choices_from_pool(equipment)
    
    for key, val in start_with.items():
        for thing in val:
            if thing not in random_settings[key]:
                random_settings[key] += [thing]


def draw_choices_from_pool(itempool):
    N = random.choices(range(len(itempool)), weights=geometric_weights(len(itempool)))[0]
    return random.sample(list(itempool.keys()), N)


def remove_plando_if_random(random_settings):
    """ For settings that have a _random option, remove the specific plando if _random is true """
    settings_to_check = ["trials", "mq_dungeons", "chicken_count", "big_poe_count"]
    for setting in settings_to_check:
        if random_settings[setting+'_random'] == "true":
            random_settings.pop(setting)


def generate_plando(weights, override_weights_fname):
    # Load the weight dictionary
    if weights == "RSL":
        weight_options, weight_dict = load_weights_file("rsl_season4.json")
    elif weights == "full-random":
        weight_options = None
        weight_dict = generate_balanced_weights(None)
    else:
        weight_options, weight_dict = load_weights_file(weights)


    # If an override_weights file name is provided, load it
    start_with = {"starting_items":[], "starting_songs":[], "starting_equipment":[]}
    if override_weights_fname is not None:
        print(f"RSL GENERATOR: LOADING OVERRIDE WEIGHTS from {override_weights_fname}")
        override_options, override_weights = load_weights_file(override_weights_fname)
        # Check for starting items, songs and equipment
        for key in start_with.keys():
            if key in override_weights.keys():
                start_with[key] = override_weights[key]
                override_weights.pop(key)

        # Replace the options
        if override_options is not None:
            for key, value in override_options.items():
                # Handling overwrite
                if not (key.startswith("extra_") or key.startswith("remove_")):
                    weight_options[key] = value
                    continue

                # Handling extras
                if key.startswith("extra_"):
                    option = key.split("extra_")[1]
                    if option not in weight_options:
                        weight_options[option] = value
                    else: # Both existing options and extra options
                        if isinstance(weight_options[option], dict):
                            weight_options[option].update(value) 
                        else:
                            weight_options[option] += value
                            weight_options[option] = list(set(weight_options[option]))

                # Handling removes
                if key.startswith("remove_"):
                    option = key.split("remove_")[1]
                    if option in weight_options:
                        for item in value:
                            if item in weight_options[option]:
                                weight_options[option].remove(item)

        # Replace the weights
        for key, value in override_weights.items():
            weight_dict[key] = value


    ####################################################################################
    # Make a new function that parses the weights file that does this stuff
    ####################################################################################
    # Generate even weights for tokens and triforce pieces given the max value (Maybe put this into the step that loads the weights)
    for nset in ["bridge_tokens", "ganon_bosskey_tokens", "triforce_goal_per_world"]:
        kw = nset + "_max"
        nmax = weight_options[kw] if kw in weight_options else 100
        weight_dict[nset] = {i+1: 100./nmax for i in range(nmax)}
        if kw in weight_dict:
            weight_dict.pop(kw)
    ####################################################################################

    # Draw the random settings
    random_settings = {}
    for setting, options in weight_dict.items():
        random_settings[setting] = random.choices(list(options.keys()), weights=list(options.values()))[0]


    # Add starting items, conditionals, tricks and excluded locations
    if weight_options is not None:
        if "conditionals" in weight_options:
            conds.parse_conditionals(weight_options["conditionals"], weight_dict, random_settings, start_with)
        if "tricks" in weight_options:
            random_settings["allowed_tricks"] = weight_options["tricks"]
        if "disabled_locations" in weight_options:
            random_settings["disabled_locations"] = weight_options["disabled_locations"]
        if "starting_items" in weight_options and weight_options["starting_items"] == True:
            draw_starting_item_pool(random_settings, start_with)

    # Remove plando if a _random setting is true
    if not (weight_options is not None and
      "allow_random_and_plando" in weight_options and
      weight_options["allow_random_and_plando"]):
        remove_plando_if_random(random_settings)

    # Format numbers and bools to not be strings
    for setting, value in random_settings.items():
        setting_type = get_setting_info(setting).type
        if setting_type is bool:
            if value == "true":
                value = True
            elif value == "false":
                value = False
            else:
                raise TypeError(f'Value for setting {setting!r} must be "true" or "false"')
        elif setting_type is int:
            value = int(value)
        elif setting_type is not str and setting not in ["allowed_tricks", "disabled_locations", "starting_items", "starting_songs", "starting_equipment", "hint_dist_user"]:
            raise NotImplementedError(f'{setting} has an unsupported setting type: {setting_type!r}')
        random_settings[setting] = value


    # Save the output plando
    output = {
        "settings": random_settings,
        "file_hash": [version_hash_1, version_hash_2, *random.choices(HASH_ICONS, k=3)]
    }

    plando_filename = f'random_settings_{datetime.datetime.utcnow():%Y-%m-%d_%H-%M-%S_%f}.json'
    # plando_filename = f'random_settings.json'

    if not os.path.isdir("data"):
        os.mkdir("data")
    with open(os.path.join("data", plando_filename), 'w') as fp:
        json.dump(output, fp, indent=4)

    return plando_filename
