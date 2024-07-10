import random

# This dict exists for two reasons,
#
# 1. I want to keep track of all of the options that I know about with this script.
# This will allow me to detect when new options are added, removed, or changed on
# an existing multiselect setting.
#
# 2. Multiselect options are now going to be fully on or fully off to vastly simplify
# how I store each setting's options and weights. Using this dict, I know all of the
# options that I must turn on when a multiselect is enabled. Any additional behavior
# will be controlled via conditionals
#
# While not all of these settings are controlled here (*_specific settings or
# misc_hints for instance), they are included here for reason 1 above to help me
# identify when changes are made to the rando code.
#
# Note: They are all listed here, but misc_hints should not be called in the multiselect
# section, but rather in the options section as we chose them to be static. Additionally,
# the settings that end with `_specific` should also not be used in the multiselect
# section. These settings will all be intentionally ignored below.
ms_option_lookup = {
    "key_rings": ["Thieves Hideout", "Treasure Chest Game", "Forest Temple",
        "Fire Temple", "Water Temple", "Shadow Temple", "Spirit Temple",
        "Bottom of the Well", "Gerudo Training Ground", "Ganons Castle"],
    "silver_rupee_pouches": ['Dodongos Cavern Staircase', 'Ice Cavern Spinning Scythe',
        'Ice Cavern Push Block', 'Bottom of the Well Basement', 'Shadow Temple Scythe Shortcut',
        'Shadow Temple Invisible Blades', 'Shadow Temple Huge Pit', 'Shadow Temple Invisible Spikes',
        'Gerudo Training Ground Slopes', 'Gerudo Training Ground Lava', 'Gerudo Training Ground Water',
        'Spirit Temple Child Early Torches', 'Spirit Temple Adult Boulders', 'Spirit Temple Lobby and Lower Adult',
        'Spirit Temple Sun Block', 'Spirit Temple Adult Climb', 'Ganons Castle Spirit Trial',
        'Ganons Castle Light Trial', 'Ganons Castle Fire Trial', 'Ganons Castle Shadow Trial',
        'Ganons Castle Water Trial', 'Ganons Castle Forest Trial'],
    "dungeon_shortcuts": ['Deku Tree', 'Dodongos Cavern', 'Jabu Jabus Belly', 'Forest Temple',
        'Fire Temple', 'Water Temple', 'Shadow Temple', 'Spirit Temple'],
    "mq_dungeons_specific": ['Deku Tree', 'Dodongos Cavern', 'Jabu Jabus Belly', 'Forest Temple',
        'Fire Temple', 'Water Temple', 'Shadow Temple', 'Spirit Temple', 'Bottom of the Well',
        'Ice Cavern', 'Gerudo Training Ground', 'Ganons Castle'],
    "empty_dungeons_specific": ['Deku Tree', 'Dodongos Cavern', 'Jabu Jabus Belly', 'Forest Temple',
        'Fire Temple', 'Water Temple', 'Shadow Temple', 'Spirit Temple'],
    "mix_entrance_pools": ["Interior", "GrottoGrave", "Dungeon", "Overworld"],
    "spawn_positions": ["child", "adult"],
    "shuffle_child_trade": ['Weird Egg', 'Chicken', 'Zeldas Letter', 'Keaton Mask', 'Skull Mask',
        'Spooky Mask', 'Bunny Hood', 'Goron Mask', 'Zora Mask', 'Gerudo Mask', 'Mask of Truth'],
    "minor_items_as_major_chest": ["bombchus", "shields", "capacity"],
    "misc_hints": ['altar', 'dampe_diary', 'ganondorf', 'warp_songs_and_owls', '10_skulltulas',
        '20_skulltulas', '30_skulltulas', '40_skulltulas', '50_skulltulas', 'frogs2', 'mask_shop',
        'unique_merchants'],
    "adult_trade_start": ['Pocket Egg', 'Pocket Cucco', 'Cojiro', 'Odd Mushroom', 'Odd Potion',
        'Poachers Saw', 'Broken Sword', 'Prescription', 'Eyeball Frog', 'Eyedrops', 'Claim Check']
}

invalid_settings = ["mq_dungeons_specific", "empty_dungeons_specific", "misc_hints"]


def _validate_ms_weights(ms_weights):
    for setting in ms_weights.keys():
        if setting not in ms_option_lookup.keys():
            raise Exception(f"{setting} is not a valid multiselect setting.")
    if "misc_hints" in ms_weights:
        raise Exception("misc_hints should only be defined in the options section.")
    for setting in invalid_settings:
        if setting in ms_weights:
            raise Exception(f"Randomizing {setting} is not supported.")


def resolve_multiselects(ms_weights):
    randomized_ms = { setting: [] for setting in invalid_settings }
    _validate_ms_weights(ms_weights)

    for setting, options in ms_option_lookup.items():
        if setting in invalid_settings:
            continue
        if random.random()*100 < ms_weights[setting]:
            randomized_ms[setting] = options
        else:
            randomized_ms[setting] = []

    return randomized_ms