import random
import json
import os
import sys
from decimal import Decimal, ROUND_UP

from multiselects import ms_option_lookup
from utils import geometric_weights, string_to_int


def parse_conditionals(conditional_list, weight_dict, random_settings, extra_starting_items):
    """ Parse the conditionals in the weights file to enable/disable them """
    for cond, details in conditional_list.items():
        if details[0]:
            getattr(sys.modules[__name__], cond)(random_settings, weight_dict=weight_dict, extra_starting_items=extra_starting_items, cparams=details[1:])


def constant_triforce_hunt_extras(random_settings, weight_dict, **kwargs):
    """ Keep constant 25% extra Triforce Pieces for all item pools. """
    random_settings['triforce_count_per_world'] = int(Decimal(random_settings['triforce_goal_per_world'] * 1.25).to_integral_value(rounding=ROUND_UP))


def exclude_minimal_triforce_hunt(random_settings, weight_dict, **kwargs):
    """ If triforce hunt is enabled, reroll the item pool excluding minimal. """
    weights = weight_dict['item_pool_value']
    if 'minimal' in weights.keys() and random_settings['triforce_hunt'] == "true":
        weights.pop('minimal')
    random_settings['item_pool_value'] = random.choices(list(weights.keys()), weights=list(weights.values()))[0]


def exclude_ice_trap_misery(random_settings, weight_dict, **kwargs):
    """ If the damage multiplier is quad or OHKO, exclude ice trap onslaught and mayhem. """
    weights = weight_dict['junk_ice_traps']
    if 'mayhem' in weights.keys() and random_settings['damage_multiplier'] in ['quadruple', 'ohko']:
        weights.pop('mayhem')
    if 'onslaught' in weights.keys() and random_settings['damage_multiplier'] in ['quadruple', 'ohko']:
        weights.pop('onslaught')
    random_settings['junk_ice_traps'] = random.choices(list(weights.keys()), weights=list(weights.values()))[0]


def disable_pot_chest_texture_independence(random_settings, **kwargs):
    """ Set correct_potcrate_appearances to match correct_chest_appearances. """
    if random_settings['correct_chest_appearances'] in ['textures', 'both', 'classic']:
        random_settings['correct_potcrate_appearances'] = 'textures_content'
    else:
        random_settings['correct_potcrate_appearances'] = 'off'


def disable_keysanity_independence(random_settings, **kwargs):
    """ Set shuffle_hideoutkeys and shuffle_tcgkeys to match shuffle_smallkeys. """
    if random_settings['shuffle_smallkeys'] == 'remove':
        random_settings['shuffle_hideoutkeys'] = 'vanilla'
        # random_settings['shuffle_tcgkeys'] = 'remove'

    elif random_settings['shuffle_smallkeys'] in ['vanilla', 'dungeon']:
        random_settings['shuffle_hideoutkeys'] = 'vanilla'
        # random_settings['shuffle_tcgkeys'] = 'vanilla'

    else:
        random_settings['shuffle_hideoutkeys'] = random_settings['shuffle_smallkeys']
        # random_settings['shuffle_tcgkeys'] = random_settings['shuffle_smallkeys']


def restrict_one_entrance_randomizer(random_settings, **kwargs):
    """ Ensure only a single pool is shuffled. If more than 1 is shuffled, randomly select one to keep and disable the rest. """
    erlist = ["shuffle_interior_entrances:off", "shuffle_grotto_entrances:false", "shuffle_dungeon_entrances:off", "shuffle_overworld_entrances:false"]

    # Count how many ER are on
    enabled_er = []
    for item in erlist:
        setting, off_option = item.split(":")
        if random_settings[setting] != off_option:
            enabled_er.append(setting)

    # If too many are enabled, chose one to keep on
    if len(enabled_er) < 2:
        return
    keepon = random.choice(enabled_er).split(":")[0]

    # Turn the rest off
    for item in erlist:
        setting, off_option = item.split(":")
        if setting != keepon:
            random_settings[setting] = off_option


def random_scrubs_start_wallet(random_settings, weight_dict, extra_starting_items, **kwargs):
    """ If random scrubs is enabled, add a wallet to the extra starting items """
    if random_settings['shuffle_scrubs'] == 'random':
        extra_starting_items['starting_equipment'] += ['wallet']


def shuffle_goal_hints(random_settings, **kwargs):
    """ Swaps Way of the Hero hints with Goal hints. Takes an extra input [how often to swap] """
    chance_of_goals = string_to_int(kwargs['cparams'][0])
    current_distro = random_settings['hint_dist']

    # Roll to swap goal hints
    goals = random.choices([True, False], weights=[chance_of_goals, 100-chance_of_goals])[0]
    if not goals or current_distro == 'useless':
        return

    # Load the distro
    with open(os.path.join('randomizer', 'data', 'Hints', current_distro+'.json')) as fin:
        distroin = json.load(fin)

    # Perform the swap
    woth = {**distroin['distribution']['woth']}
    distroin['distribution']['woth'] = distroin['distribution']['goal']
    distroin['distribution']['goal'] = woth
    random_settings['hint_dist_user'] = distroin


def replace_dampe_diary_hint_with_lightarrow(random_settings, **kwargs):
    """ Replace the dampe diary hint with a Light Arrow hint """
    current_distro = random_settings['hint_dist']

    # Load the distro and change the misc hint
    with open(os.path.join('randomizer', 'data', 'Hints', current_distro+'.json')) as fin:
        distroin = json.load(fin)
    distroin['misc_hint_items'] = {'dampe_diary': "Light Arrows"}
    random_settings['hint_dist_user'] = distroin


def split_collectible_bridge_conditions(random_settings, **kwargs):
    """ Split heart and skulltula token bridge and ganon boss key.
    kwargs: [how often to have a heart or skull bridge, "heart%/skull%", "bridge%/gbk%/both"]
    """
    chance_of_collectible_wincon = string_to_int(kwargs['cparams'][0])
    typeweights = [int(x) for x in kwargs['cparams'][1].split('/')]
    weights = [int(x) for x in kwargs['cparams'][2].split('/')]

    # Roll for collectible win condition
    skull_wincon = random.choices([True, False], weights=[chance_of_collectible_wincon, 100-chance_of_collectible_wincon])[0]
    if not skull_wincon:
        return

    # Roll for hearts or skulls
    condition = random.choices(["hearts", "tokens"], weights=typeweights)[0]

    # Roll for bridge/bosskey/both
    whichtype = random.choices(['bridge', 'gbk', 'both'], weights=weights)[0]
    if whichtype in ['bridge', 'both']:
        random_settings['bridge'] = condition
    if whichtype in ['gbk', 'both']:
        random_settings['shuffle_ganon_bosskey'] = condition



def adjust_chaos_hint_distro(random_settings, **kwargs):
    """ Duplicates the always hints in the chaos hint distro and removes
    the double chance at each sometimes hint """

    # Load the dist
    if 'hint_dist_user' in random_settings:
        distroin = random_settings['hint_dist_user']
        if not distroin['name'] == "chaos":
            print("Not using the chaos distribution, passing...")
            return
    else:
        current_distro = random_settings['hint_dist']
        if not current_distro == "chaos":
            print("Not using the chaos distribution, passing...")
            return
        with open(os.path.join('randomizer', 'data', 'Hints', current_distro+'.json')) as fin:
            distroin = json.load(fin)

    # Make changes and save
    distroin['distribution']['always']['copies'] = 2
    distroin['distribution']['overworld']['weight'] = 0
    distroin['distribution']['dungeon']['weight'] = 0
    distroin['distribution']['song']['weight'] = 0
    random_settings['hint_dist_user'] = distroin



def exclude_mapcompass_info_remove(random_settings, weight_dict, **kwargs):
    """ If Maps and Compai give info, do not allow them to be removed """
    weights = weight_dict['shuffle_mapcompass']
    if 'remove' in weights.keys() and random_settings['enhance_map_compass'] == "true":
        weights.pop('remove')
    random_settings['shuffle_mapcompass'] = random.choices(list(weights.keys()), weights=list(weights.values()))[0]



def ohko_starts_with_nayrus(random_settings, weight_dict, extra_starting_items, **kwargs):
    """ If one hit ko is enabled, add Nayru's Love to the starting items """
    if random_settings['damage_multiplier'] == 'ohko':
        extra_starting_items['starting_inventory'] += ['nayrus_love']

def invert_dungeons_mq_count(random_settings, weight_dict, **kwargs):
    """ When activated will invert the MQ dungeons count
        kwargs: [chance of having the MQ count inverted]
    """
    if random_settings['mq_dungeons_mode'] != 'count':
        return

    chance_of_inverting_mq_count = string_to_int(kwargs['cparams'][0])
    invert_mq_count = random.choices([True, False], weights=[chance_of_inverting_mq_count, 100-chance_of_inverting_mq_count])[0]

    if not invert_mq_count:
        return

    current_mq_dungeons_count = int(random_settings['mq_dungeons_count'])
    new_mq_dungeons_count = 12 - current_mq_dungeons_count

    random_settings['mq_dungeons_count'] = new_mq_dungeons_count


def shuffle_valley_lake_exit(random_settings, **kwargs):
    """ If both OWER and owl shuffle are on, shuffle the gerudo valley -> lake entrance """
    if random_settings['shuffle_overworld_entrances'] == 'true'and random_settings['owl_drops'] == 'true':
        random_settings['shuffle_gerudo_valley_river_exit'] = "true"


def select_one_pots_crates_freestanding(random_settings, **kwargs):
    chance_one_is_on = string_to_int(kwargs['cparams'][0])
    setting_weights = [int(x) for x in kwargs['cparams'][1].split('/')]
    weights = [int(x) for x in kwargs['cparams'][2].split('/')]

    # If setting is randomized off, return
    if not (random.randint(0, 100) < chance_one_is_on):
       return

    # Choose which of the settings to turn on
    setting = random.choices(["shuffle_pots", "shuffle_crates", "shuffle_freestanding_items"], weights=setting_weights)[0]
    random_settings[setting] = random.choices(["overworld", "dungeons", "all"], weights=weights)[0]


def geometrically_draw_dungeon_shortcuts(random_settings, **kwargs):
    nunique = len(ms_option_lookup["dungeon_shortcuts"])
    chooseN = random.choices(range(nunique+1), weights=geometric_weights(nunique+1))[0]
    random_settings["dungeon_shortcuts"] = random.sample(ms_option_lookup["dungeon_shortcuts"], chooseN)


def limit_overworld_entrances_in_mixed_entrance_pools(random_settings, **kwargs):
    if len(random_settings["mix_entrance_pools"]) < 1:
        return

    # Decide if overworld should be included
    overworld_probability = string_to_int(kwargs['cparams'][0])
    includeOverworld = random.random()*100 < overworld_probability
    # If needed, remove overworld from mixed pools
    if not includeOverworld and "Overworld" in random_settings["mix_entrance_pools"]:
        random_settings["mix_entrance_pools"].remove("Overworld")


def limit_mixed_pool_entrances(random_settings, **kwargs):
    max_mixed = int(kwargs['cparams'][0])
    omit_overworld = bool(kwargs['cparams'][1])
    if omit_overworld and "Overworld" in random_settings["mix_entrance_pools"]:
        random_settings["mix_entrance_pools"].remove("Overworld")
    if len(random_settings["mix_entrance_pools"]) > max_mixed:
        random_settings["mix_entrance_pools"] = random.sample(random_settings["mix_entrance_pools"], max_mixed)


def keysanity_key_get_keyrings(random_settings, **kwargs):
    if random_settings['shuffle_smallkeys'] == 'keysanity':
        random_settings['key_rings'] = ms_option_lookup["key_rings"]