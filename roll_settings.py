import os
import sys
import datetime
import json
import random
import conditionals as conds
from multiselects import resolve_multiselects, ms_option_lookup
from rslversion import __version__
sys.path.append("randomizer")
from randomizer.ItemPool import trade_items, child_trade_items
from randomizer.SettingsList import get_settings_from_tab, get_settings_from_section, SettingInfos
from randomizer.StartingItems import inventory, songs, equipment
from utils import geometric_weights

def get_setting_info(setting_name):
    """ Quick replacement for removed function in the randomizer. """
    return SettingInfos.setting_infos[setting_name]


def load_weights_file(weights_fname):
    """ Given a weights filename, open it up. If the file does not exist, make it with even weights """
    fpath = os.path.join(weights_fname)
    if os.path.isfile(fpath):
        with open(fpath) as fin:
            datain = json.load(fin)
    return parse_weights(datain)


def parse_weights(datain):
    weight_options = datain["options"] if "options" in datain else None
    conditionals = datain["conditionals"] if "conditionals" in datain else None
    weight_multiselect = datain["multiselect"] if "multiselect" in datain else None
    weight_dict = datain["weights"]

    return weight_options, conditionals, weight_multiselect, weight_dict


def generate_balanced_weights(fname="default_weights.json"):
    """ Generate a file with even weights for each setting. """
    settings_to_randomize = list(get_settings_from_tab("main_tab"))[1:] + \
                list(get_settings_from_tab("detailed_tab")) + \
                list(get_settings_from_tab("other_tab")) + \
                list(get_settings_from_tab("starting_tab"))

    exclude_from_weights = ["bridge_tokens", "ganon_bosskey_tokens", "bridge_hearts", "ganon_bosskey_hearts",
                            "triforce_goal_per_world", "triforce_count_per_world", "disabled_locations",
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


def draw_starting_item_pool(random_settings, start_with):
    """ Select starting items, songs, and equipment. """
    random_settings["starting_inventory"] = draw_choices_from_pool({
        name: info
        for name, info in inventory.items()
        if (info.item_name not in trade_items or info.item_name in random_settings["adult_trade_start"])
        and (info.item_name not in child_trade_items or info.item_name in random_settings["shuffle_child_trade"] or info.item_name == 'Zeldas Letter')
    })
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
    settings_to_check = ["trials", "chicken_count", "big_poe_count"]
    for setting in settings_to_check:
        if random_settings[setting+'_random'] == "true":
            random_settings.pop(setting)


def remove_redundant_settings(random_settings):
    """ Disable settings that the randomizer expects to be disabled.
    The randomizer will reject plandos with disabled settings set to non-default values.
    Settings are considered disabled if they are disabled in the randomizer GUI by another setting.
    """
    settings_list = list(random_settings.keys())
    for setting in settings_list:
        # As we're iterating, the setting may already have been deleted/disabled by a previous setting
        if setting in random_settings.keys():
            info = get_setting_info(setting)
            choice = random_settings[setting]
            if info.disable is not None:
                for option, disabling in info.disable.items():
                    negative = False
                    if isinstance(option, str) and option[0] == '!':
                        negative = True
                        option = option[1:]
                    if (choice == option) != negative:
                        for other_setting in disabling.get('settings', []):
                            remove_disabled_setting(random_settings, other_setting)
                        for section in disabling.get('sections', []):
                            for other_setting in get_settings_from_section(section):
                                remove_disabled_setting(random_settings, other_setting)
                        for tab in disabling.get('tabs', []):
                            for other_setting in get_settings_from_tab(tab):
                                remove_disabled_setting(random_settings, other_setting)


def remove_disabled_setting(random_settings, other_setting):
    if other_setting in random_settings.keys():
        random_settings.pop(other_setting)


def draw_dungeon_shortcuts(random_settings):
    """ Decide how many dungeon shortcuts to enable and randomly select them """
    N = random.choices(range(8), weights=geometric_weights(8))[0]
    dungeon_shortcuts_opts = ['deku_tree', 'dodongos_cavern', 'jabu_jabus_belly', 'forest_temple', 'fire_temple', 'shadow_temple', 'spirit_temple']
    random_settings["dungeon_shortcuts"] = random.sample(dungeon_shortcuts_opts, N)


def generate_weights_override(weights, override_weights_fname):
    # Load the weight dictionary
    if weights == "RSL":
        weight_options, conditionals, weight_multiselect, weight_dict = load_weights_file("weights/rsl_season7.json")
    elif weights == "full-random":
        weight_options = None
        weight_dict = generate_balanced_weights(None)
    else:
        weight_options, conditionals, weight_multiselect, weight_dict = load_weights_file(weights)


    # If an override_weights file name is provided, load it
    start_with = {"starting_inventory":[], "starting_songs":[], "starting_equipment":[]}
    if override_weights_fname is not None:
        if override_weights_fname == '-':
            print("RSL GENERATOR: LOADING OVERRIDE WEIGHTS from standard input")
            override_options, override_conditionals, override_multiselect, override_weights = parse_weights(json.load(sys.stdin))
        else:
            print(f"RSL GENERATOR: LOADING OVERRIDE WEIGHTS from {override_weights_fname}")
            override_options, override_conditionals, override_multiselect, override_weights = load_weights_file(override_weights_fname)
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

        # Replace the conditionals
        if override_conditionals is not None:
            for name, state in override_conditionals.items():
                conditionals[name] = state

        # Replace the multiselects
        if override_multiselect is not None:
            for key, value in override_multiselect.items():
                weight_multiselect[key] = value

    return weight_options, conditionals, weight_multiselect, weight_dict, start_with


def generate_plando(weights, override_weights_fname, no_seed):
    weight_options, conditionals, weight_multiselects, weight_dict, start_with = generate_weights_override(weights, override_weights_fname)

    ####################################################################################
    # Make a new function that parses the weights file that does this stuff
    ####################################################################################
    # Generate even weights for tokens, hearts, and triforce pieces given the max value (Maybe put this into the step that loads the weights)
    for nset in ["bridge_tokens", "ganon_bosskey_tokens", "bridge_hearts", "ganon_bosskey_hearts", "triforce_goal_per_world", "triforce_count_per_world"]:
        kwx = nset + "_max"
        kwn = nset + "_min"
        nmax = weight_options[kwx] if kwx in weight_options else 100
        nmin = weight_options[kwn] if kwn in weight_options else 1
        weight_dict[nset] = {i: 100./(nmax - nmin + 1) for i in range(nmin, nmax + 1)}
        if kwx in weight_dict:
            weight_dict.pop(kwx)
        if kwn in weight_dict:
            weight_dict.pop(kwn)
    ####################################################################################

    # Draw the random settings
    random_settings = {}
    for setting, options in weight_dict.items():
        random_settings[setting] = random.choices(list(options.keys()), weights=list(options.values()))[0]

    # Draw the multiselects
    if weight_multiselects is not None:
        random_settings.update(resolve_multiselects(weight_multiselects))

    # Set the conditionals
    if conditionals is not None:
        conds.parse_conditionals(conditionals, weight_dict, random_settings, start_with)

    # Add starting items, tricks, and excluded locations
    if weight_options is not None:
        # if "conditionals" in weight_options:
        #     conds.parse_conditionals(weight_options["conditionals"], weight_dict, random_settings, start_with)
        if "tricks" in weight_options:
            random_settings["allowed_tricks"] = weight_options["tricks"]
        if "disabled_locations" in weight_options:
            random_settings["disabled_locations"] = weight_options["disabled_locations"]
        random_settings["misc_hints"] = weight_options["misc_hints"] if "misc_hints" in weight_options else []
        if "starting_items" in weight_options and weight_options["starting_items"] == True:
            draw_starting_item_pool(random_settings, start_with)

    # Remove plando setting if a _random setting is true
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
        elif setting_type is not str and setting not in ["allowed_tricks", "disabled_locations", "starting_inventory", "misc_hints", "starting_songs", "starting_equipment", "hint_dist_user", "dungeon_shortcuts"] + list(ms_option_lookup.keys()):
            raise NotImplementedError(f'{setting} has an unsupported setting type: {setting_type!r}')
        random_settings[setting] = value

    # Remove conflicting "dead" settings since rando won't ignore them anymore
    remove_redundant_settings(random_settings)

    # Add the RSL Script version to the plando
    random_settings['user_message'] = f'RSL Script v{__version__}'

    # Save the output plando
    output = {"settings": random_settings}

    plando_filename = f'random_settings_{datetime.datetime.utcnow():%Y-%m-%d_%H-%M-%S_%f}.json'
    # plando_filename = f'random_settings.json'

    if not os.path.isdir("data"):
        os.mkdir("data")
    with open(os.path.join("data", plando_filename), 'w') as fp:
        json.dump(output, fp, indent=4)
    if no_seed:
        print(f"Plando File: {plando_filename}")

    return plando_filename
