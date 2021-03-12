import os
import sys
import json
import random
import conditionals as conds
from version import version_hash_1, version_hash_2
sys.path.append("randomizer")
from randomizer.SettingsList import get_settings_from_tab, get_setting_info
from randomizer.StartingItems import inventory, songs, equipment
from randomizer.Spoiler import HASH_ICONS


STANDARD_TRICKS = True # Whether or not to enable all of the tricks in Standard settings
RSL_TRICKS = True # Add the extra tricks that we enable for rando rando
STARTING_ITEMS = True # Draw starting items, songs, and equipment from a geometric distribution

BROKEN_SETTINGS = [] # If any settings are broken, add their name here and they will be non-randomized


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

    exclude_from_weights = ["bridge_tokens", "lacs_tokens", "triforce_goal_per_world", "disabled_locations",
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


def add_standard_tricks(random_settings):
    """ Add the tricks enabled in standard to the plando. """
    random_settings["randomize_settings"] = False
    random_settings["disabled_locations"] = []
    random_settings["allowed_tricks"] = ["logic_fewer_tunic_requirements", "logic_grottos_without_agony",
        "logic_child_deadhand", "logic_man_on_roof", "logic_dc_jump", "logic_rusted_switches", "logic_windmill_poh",
        "logic_crater_bean_poh_with_hovers", "logic_forest_vines", "logic_goron_city_pot_with_strength",
        "logic_lens_botw", "logic_lens_castle", "logic_lens_gtg", "logic_lens_shadow",
        "logic_lens_shadow_back", "logic_lens_spirit"]


def add_rsl_tricks(random_settings):
    """ Add some extra tricks to the plando that are beyond the scope of Standard. """
    random_settings["allowed_tricks"] = random_settings["allowed_tricks"] + ["logic_visible_collisions", 
        "logic_deku_b1_webs_with_bow", "logic_lens_gtg_mq", "logic_lens_jabu_mq", "logic_lens_shadow_mq",
        "logic_lens_shadow_mq_back", "logic_lens_spirit_mq"]



def generate_plando(weights, override_weights_fname):
    # Load the weight dictionary
    if weights == "RSL":
        weight_options, weight_dict = load_weights_file("random_settings_league_s2.json")
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
                if not key.startswith("extra_"): # Overwrite
                    weight_options[key] = value
                elif key.split("extra_")[1] not in weight_options: # If its extra but key isnt there
                    weight_options[key.split("extra_")[1]] = value
                else: # Both existing options and extra options
                    weight_options[key.split("extra_")[1]].update(value) 

        # Replace the weights
        for key, value in override_weights.items():
            weight_dict[key] = value


    ####################################################################################
    # Make a new function that parses the weights file that does this stuff
    ####################################################################################
    # Generate even weights for tokens and triforce pieces given the max value (Maybe put this into the step that loads the weights)
    for nset in ["bridge_tokens", "lacs_tokens", "triforce_goal_per_world"]:
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


    # Check conditional settings for RSL
    if weight_options is not None and "conditionals" in weight_options:
        conds.parse_conditionals(weight_options["conditionals"], weight_dict, random_settings)


    # Add the tricks to the plando
    if STANDARD_TRICKS:
        add_standard_tricks(random_settings)
    if RSL_TRICKS:
        add_rsl_tricks(random_settings)


    # Draw the starting items, songs, and equipment
    if STARTING_ITEMS:
        draw_starting_item_pool(random_settings, start_with)


    # Format numbers and bools to not be strings
    for setting, value in random_settings.items():
        if value == "false":
            random_settings[setting] = False
        elif value == "true":
            random_settings[setting] = True
        else:
            try:
                random_settings[setting] = int(value)
            except:
                random_settings[setting] = value


    # Save the output plando
    output = {
        "settings": random_settings,
        "file_hash": [version_hash_1, version_hash_2, *random.choices(HASH_ICONS, k=3)]
    }

    if not os.path.isdir("data"):
        os.mkdir("data")
    with open(os.path.join("data", "random_settings.json"), 'w') as fp:
        json.dump(output, fp, indent=4)