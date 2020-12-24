import json, random, sys, os, traceback
sys.path.append('..')
from SettingsList import get_settings_from_tab, get_setting_info
from StartingItems import inventory, songs, equipment
from Spoiler import HASH_ICONS
import Conditionals as conds
from rsl_version import version_hash_1, version_hash_2, VersionError, check_rando_version
check_rando_version()

# Please set the weights file you with to load
weights = 'rrl' # The default Rando Rando League Season 2 weights
# weights = 'full-random' # Every setting with even weights
# weights = 'coop' # Uses the rrl weights with some extra modifications
# weights = 'my_weights.json' # Provide your own weights file. If the specified file does not exist, this will create one with equal weights
# mw_weights_file = 'rsl_multiworld.json' # If this variable exists, load this file and use it to edit loaded weights

COOP_SETTINGS = False # Change some settings to be more coop friendly
STANDARD_TRICKS = True # Whether or not to enable all of the tricks in Standard settings
RRL_TRICKS = True # Add the extra tricks that we enable for rando rando
RRL_CONDITIONALS = True # In rando rando we have a couple conditional cases. Ensure that they are met
STARTING_ITEMS = True # Draw starting items, songs, and equipment from a geometric distribution

BROKEN_SETTINGS = [] # If any settings are broken, add their name here and they will be non-randomized


# Handle all uncaught exceptions with logging
def error_handler(type, value, tb):
    with open('ERRORLOG.TXT', 'w') as errout:
        traceback.print_exception(type, value, tb, file=errout)
        traceback.print_exception(type, value, tb, file=sys.stdout)
sys.excepthook = error_handler


def geometric_weights(N, startat=0, rtype='list'):
    """ Compute weights according to a geometric distribution """
    if rtype == 'list':
        return [50.0/2**i for i in range(N)]
    elif rtype == 'dict':
        return {str(startat+i): 50.0/2**i for i in range(N)}


def draw_starting_item_pool(random_settings, start_with):
    """ Select starting items, songs, and equipment. """
    random_settings['starting_items'] = draw_choices_from_pool(inventory)
    random_settings['starting_songs'] = draw_choices_from_pool(songs)
    random_settings['starting_equipment'] = draw_choices_from_pool(equipment)
    
    for key, val in start_with.items():
        for thing in val:
            if thing not in random_settings[key]:
                random_settings[key] += [thing]

def draw_choices_from_pool(itempool):
    N = random.choices(range(len(itempool)), weights=geometric_weights(len(itempool)))[0]
    return random.sample(list(itempool.keys()), N)


def generate_balanced_weights(fname='default_weights.json'):
    """ Generate a file with even weights for each setting. """
    settings_to_randomize = list(get_settings_from_tab('main_tab'))[1:] + \
                list(get_settings_from_tab('detailed_tab')) + \
                list(get_settings_from_tab('other_tab')) + \
                list(get_settings_from_tab('starting_tab'))

    exclude_from_weights = ['bridge_tokens', 'lacs_tokens', 'triforce_goal_per_world', 'disabled_locations',
                            'allowed_tricks', 'starting_equipment', 'starting_items', 'starting_songs']
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
    random_settings['randomize_settings'] = False
    random_settings['disabled_locations'] = []
    random_settings['allowed_tricks'] = ["logic_fewer_tunic_requirements", "logic_grottos_without_agony",
        "logic_child_deadhand", "logic_man_on_roof", "logic_dc_jump", "logic_rusted_switches", "logic_windmill_poh",
        "logic_crater_bean_poh_with_hovers", "logic_forest_vines", "logic_goron_city_pot_with_strength",
        "logic_lens_botw", "logic_lens_castle", "logic_lens_gtg", "logic_lens_shadow",
        "logic_lens_shadow_back", "logic_lens_spirit"]


def add_rrl_tricks(random_settings):
    """ Add some extra tricks to the plando that are beyond the scope of Standard. """
    random_settings['allowed_tricks'] = random_settings['allowed_tricks'] + ["logic_visible_collisions", 
        "logic_deku_b1_webs_with_bow", "logic_lens_gtg_mq", "logic_lens_jabu_mq", "logic_lens_shadow_mq",
        "logic_lens_shadow_mq_back", "logic_lens_spirit_mq"]


def load_weights_file(weights_fname):
    """ Given a weights filename, open it up. If the file does not exist, make it with even weights """
    fpath = os.path.join('weights', weights_fname)
    try:
        with open(fpath) as fin:
            weight_dict = json.load(fin)
    except FileNotFoundError:
        generate_balanced_weights(fpath)
        print(f"{fpath} not found.\nCreating with balanced weights.", file=sys.stderr)
        print(f"Plando not generated, please try again.", file=sys.stderr)
        sys.exit(1)
    return weight_dict


def main():
    # Delete residual files from previous runs
    remove_me = ['blind_random_settings.json', 'ERRORLOG.TXT']
    for file_to_delete in remove_me:
        try:
            os.remove(file_to_delete)
        except FileNotFoundError:
            pass


    # Load the weight dictionary
    if weights in ['rrl', 'coop']:
        weight_dict = load_weights_file('rando_rando_league_s2.json')
        if weight_dict['hash']['obj1'] != version_hash_1 or weight_dict['hash']['obj2'] != version_hash_2:
            raise VersionError("weights file")
        weight_dict.pop('hash')
    elif weights == 'full-random':
        weight_dict = generate_balanced_weights(None)
    else:
        weight_dict = load_weights_file(weights)


    # If a multiworld weights file is supplied, make appropriate changes
    start_with = {'starting_items':[], 'starting_songs':[], 'starting_equipment':[]}
    if "mw_weights_file" in globals():
        mw_weights = load_weights_file(mw_weights_file)
        # Check for starting items, songs and equipment
        for key in start_with.keys():
            if key in mw_weights.keys():
                start_with[key] = mw_weights[key]
                mw_weights.pop(key)

        # Replace the weights
        for mwkey, mwval in mw_weights.items():
            weight_dict[mwkey] = mwval


    # If its a co-op seed, make some small changes to weights
    if weights == 'coop':
        weight_dict['bridge_tokens'] = {i+1: 2.0 for i in range(50)}
        weight_dict['lacs_tokens'] = {i+1: 2.0 for i in range(50)}
        weight_dict['mq_dungeons_random'] = {"false": 100}
        weight_dict['mq_dungeons'] = {"0": 100,}
        weight_dict['damage_multiplier'] = {"normal": 100}


    # Check if bridge_tokens, lacs_tokens, or triforce piece count is set already, if not draw uniformly.
    number_settings = ['bridge_tokens', 'lacs_tokens', 'triforce_goal_per_world']
    for nset in number_settings:
        if not nset in weight_dict:
            weight_dict[nset] = {i+1: 1.0 for i in range(100)}


    # Draw the random settings
    random_settings = {}
    for setting, options in weight_dict.items():
        if isinstance(options, dict): # Skip settings that are hardcoded lists, like starting_items
            random_settings[setting] = random.choices(list(options.keys()), weights=list(options.values()))[0]


    # Check conditional settings for rrl
    if RRL_CONDITIONALS:
        conds.exclude_minimal_triforce_hunt(weight_dict, random_settings)
        conds.exclude_ice_trap_misery(weight_dict, random_settings)
        conds.disable_fortresskeys_independence(random_settings)


    # Add the tricks to the plando
    if STANDARD_TRICKS:
        add_standard_tricks(random_settings)
    if RRL_TRICKS:
        add_rrl_tricks(random_settings)


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
        'settings': random_settings,
        'file_hash': [version_hash_1, version_hash_2, *random.choices(HASH_ICONS, k=3)]
    }
    with open('blind_random_settings.json', 'w') as fp:
        json.dump(output, fp, indent=4)


if __name__ == '__main__':
    main()
