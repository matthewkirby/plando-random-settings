import random


def parse_conditionals(conditional_list, weight_dict, random_settings):
    """ Parse the conditionals in the weights file to enable/disable them """
    for cond, conditional_is_on in conditional_list.items():
        if conditional_is_on:
            eval(cond + "(weight_dict, random_settings)")


def exclude_minimal_triforce_hunt(weight_dict, random_settings):
    """ If triforce hunt is enabled, reroll the item pool excluding minimal. """
    weights = weight_dict['item_pool_value']
    if 'minimal' in weights.keys() and random_settings['triforce_hunt'] == "true":
        weights.pop('minimal')
    random_settings['item_pool_value'] = random.choices(list(weights.keys()), weights=list(weights.values()))[0]


def exclude_ice_trap_misery(weight_dict, random_settings):
    """ If the damage multiplier is quad or OHKO, exclude ice trap onslaught and mayhem. """
    weights = weight_dict['junk_ice_traps']
    if 'mayhem' in weights.keys() and random_settings['damage_multiplier'] in ['quadruple', 'ohko']:
        weights.pop('mayhem')
    if 'onslaught' in weights.keys() and random_settings['damage_multiplier'] in ['quadruple', 'ohko']:
        weights.pop('onslaught')
    random_settings['junk_ice_traps'] = random.choices(list(weights.keys()), weights=list(weights.values()))[0]


def disable_hideoutkeys_independence(_, random_settings):
    """ Set shuffle_hideoutkeys to match shuffle_smallkeys. """
    if random_settings['shuffle_smallkeys'] in ['remove', 'vanilla', 'dungeon']:
        random_settings['shuffle_hideoutkeys'] = 'vanilla'
    else:
        random_settings['shuffle_hideoutkeys'] = random_settings['shuffle_smallkeys']


def restrict_one_entrance_randomizer(_, random_settings):
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

def workaround_th_scz_bug(weight_dict, random_settings):
    """ Makes sure https://github.com/TestRunnerSRL/OoT-Randomizer/issues/1331 won't happen. """
    weights = weight_dict['triforce_goal_per_world']
    if random_settings['triforce_hunt'] and random_settings['triforce_goal_per_world'] == 1 and random_settings['shuffle_song_items'] == 'any' and random_settings['skip_child_zelda']:
        weights.pop(1)
        random_settings['triforce_goal_per_world'] = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
