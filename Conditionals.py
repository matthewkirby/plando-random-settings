import random

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

def disable_fortresskeys_independence(random_settings):
    """ Set shuffle_fortresskeys to match shuffle_smallkeys. """
    if random_settings['shuffle_smallkeys'] in ['remove', 'vanilla', 'dungeon']:
        random_settings['shuffle_fortresskeys'] = 'vanilla'
    else:
        random_settings['shuffle_fortresskeys'] = random_settings['shuffle_smallkeys']