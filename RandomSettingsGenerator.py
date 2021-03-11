import json, random, sys, os, traceback, argparse
import rsl_tools as tools
import conditionals as conds
from version import version_hash_1, version_hash_2
tools.check_version()
sys.path.append("randomizer")
from randomizer.SettingsList import get_settings_from_tab, get_setting_info
from randomizer.StartingItems import inventory, songs, equipment
from randomizer.Spoiler import HASH_ICONS

# Please set the weights file you with to load
weights = "RSL" # The default Random Settings League Season 2 weights
# weights = "full-random" # Every setting with even weights
# weights = "my_weights.json" # Provide your own weights file. If the specified file does not exist, this will create one with equal weights
# global_override_fname = "multiworld_override.json"
# global_override_fname = "ddr_override.json"
# global_override_fname = "beginner_override.json"
# global_override_fname = "coop_override.json"

STANDARD_TRICKS = True # Whether or not to enable all of the tricks in Standard settings
RSL_TRICKS = True # Add the extra tricks that we enable for rando rando
RSL_CONDITIONALS = True # In rando rando we have a couple conditional cases. Ensure that they are met
STARTING_ITEMS = True # Draw starting items, songs, and equipment from a geometric distribution

BROKEN_SETTINGS = [] # If any settings are broken, add their name here and they will be non-randomized


# Handle all uncaught exceptions with logging
def error_handler(type, value, tb):
    with open("ERRORLOG.TXT", 'w') as errout:
        traceback.print_exception(type, value, tb, file=errout)
        traceback.print_exception(type, value, tb, file=sys.stdout)
sys.excepthook = error_handler


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


def load_weights_file(weights_fname, override_file=False):
    """ Given a weights filename, open it up. If the file does not exist, make it with even weights """
    fpath = os.path.join("weights", weights_fname)
    if os.path.isfile(fpath):
        with open(fpath) as fin:
            weight_dict = json.load(fin)
    elif not override_file:
        print(f"{fpath} not found.\nCreating with balanced weights.", file=sys.stderr)
        generate_balanced_weights(fpath)
        sys.exit(1)
    return weight_dict


def generate_plando(override_weights_fname):
    # Delete residual files from previous runs
    remove_me = [os.path.join("data", "random_settings.json"), "ERRORLOG.TXT"]
    for file_to_delete in remove_me:
        if os.path.isfile(file_to_delete):
            os.remove(file_to_delete)


    # Load the weight dictionary
    if weights == "RSL":
        weight_dict = load_weights_file("random_settings_league_s2.json")
    elif weights == "full-random":
        weight_dict = generate_balanced_weights(None)
    else:
        weight_dict = load_weights_file(weights)


    # If an override_weights file name is provided, load it
    start_with = {"starting_items":[], "starting_songs":[], "starting_equipment":[]}
    if override_weights_fname is not None:
        print(f"RSL GENERATOR: LOADING OVERRIDE WEIGHTS from {override_weights_fname}")
        override_weights = load_weights_file(override_weights_fname, override_file=True)
        # Check for starting items, songs and equipment
        for key in start_with.keys():
            if key in override_weights.keys():
                start_with[key] = override_weights[key]
                override_weights.pop(key)

        # Replace the weights
        for mwkey, mwval in override_weights.items():
            weight_dict[mwkey] = mwval


    # Generate even weights for tokens and triforce pieces given the max value
    for nset in ["bridge_tokens", "lacs_tokens", "triforce_goal_per_world"]:
        nmax = weight_dict[nset + "_max"]
        weight_dict[nset] = {i+1: 100./nmax for i in range(nmax)}
        weight_dict.pop(nset + "_max")


    # Draw the random settings
    random_settings = {}
    for setting, options in weight_dict.items():
        random_settings[setting] = random.choices(list(options.keys()), weights=list(options.values()))[0]


    # Check conditional settings for RSL
    if RSL_CONDITIONALS:
        conds.exclude_minimal_triforce_hunt(weight_dict, random_settings)
        conds.exclude_ice_trap_misery(weight_dict, random_settings)
        conds.disable_fortresskeys_independence(random_settings)
        conds.disable_lacs_condition_ifnot_ganonbosskey(random_settings)


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


def get_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_seed", help="Suppresses the generation of a patch file.", action="store_true")
    parser.add_argument("--override", help="Use the specified weights file over the default RSL weights.")
    parser.add_argument("--worldcount", help="Generate a seed with more than 1 world.")
    parser.add_argument("--check_new_settings", help="When the version updates, run with this flag to find changes to settings names or new settings.", action="store_true")
    
    args = parser.parse_args()

    # Parse weights override file
    if args.override is not None:
        if "global_override_fname" in globals():
            raise RuntimeError("RSL GENERATOR ERROR: OVERRIDE PROVIDED AS GLOBAL AND VIA COMMAND LINE.")
        if not os.path.isfile(os.path.join("weights", args.override)):
            raise FileNotFoundError("RSL GENERATOR ERROR: CANNOT FIND SPECIFIED OVERRIDE FILE IN DIRECTORY: weights")
        override = args.override
    elif "global_override_fname" in globals():
        override = global_override_fname
    else:
        override = None

    # Parse multiworld world count
    worldcount = 1
    if args.worldcount is not None:
        worldcount = int(args.worldcount)

    return args.no_seed, worldcount, override, args.check_new_settings


def main():
    no_seed, worldcount, check_new_settings = get_command_line_args()

    if check_new_settings:
        tools.check_for_setting_changes(load_weights_file("random_settings_league_s2.json"), generate_balanced_weights(None))
        return

    max_retries = 3
    for i in range(max_retries):
        generate_plando(override_weights_fname)
        tools.init_randomizer_settings(worldcount=worldcount)
        completed_process = tools.generate_patch_file() if not no_seed else None
        if completed_process is None or completed_process.returncode == 0:
            break
        if i == max_retries-1 and completed_process.returncode != 0:
            raise RuntimeError(completed_process.stderr.decode("utf-8"))

    if not no_seed:
        print(completed_process.stderr.decode("utf-8").split("Patching ROM.")[-1])


if __name__ == "__main__":
    main()
