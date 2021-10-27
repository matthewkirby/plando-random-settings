import random
import json
import os


def parse_conditionals(conditional_list, weight_dict, random_settings, extra_starting_items):
    """ Parse the conditionals in the weights file to enable/disable them """
    for cond, details in conditional_list.items():
        if details[0]:
            eval(cond + "(random_settings, weight_dict=weight_dict, extra_starting_items=extra_starting_items, cparams=details[1:])")


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


def disable_hideoutkeys_independence(random_settings, **kwargs):
    """ Set shuffle_hideoutkeys to match shuffle_smallkeys. """
    if random_settings['shuffle_smallkeys'] in ['remove', 'vanilla', 'dungeon']:
        random_settings['shuffle_hideoutkeys'] = 'vanilla'
    else:
        random_settings['shuffle_hideoutkeys'] = random_settings['shuffle_smallkeys']


def restrict_one_entrance_randomizer(random_settings, **kwargs):
    erlist = ["shuffle_interior_entrances:off", "shuffle_grotto_entrances:false", "shuffle_dungeon_entrances:false", "shuffle_overworld_entrances:false"]

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


def dynamic_skulltula_wincon(random_settings, **kwargs):
    """ Rolls skull win condition seperately. Takes extra inputs [weight of skull win con, "bridge%/gbk%/both"] """
    chance_of_skull_wincon = int(kwargs['cparams'][0])
    weights = [int(x) for x in kwargs['cparams'][1].split('/')]

    # Roll for a skull win condition
    skull_wincon = random.choices([True, False], weights=[chance_of_skull_wincon, 100-chance_of_skull_wincon])[0]
    if not skull_wincon:
        return
    
    # Roll for bridge/bosskey/both
    whichtype = random.choices(['bridge', 'gbk', 'both'], weights=weights)[0]
    if whichtype in ['bridge', 'both']:
        random_settings['bridge'] = 'tokens'
    if whichtype in ['gbk', 'both']:
        random_settings['shuffle_ganon_bosskey'] = 'tokens'


def shuffle_goal_hints(random_settings, **kwargs):
    """ Swaps Way of the Hero hints with Goal hints. Takes an extra input [how often to swap] """
    chance_of_goals = int(kwargs['cparams'][0])
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