import json
import random
from SettingsList import logic_tricks, setting_infos, get_settings_from_tab, get_setting_info
from LocationList import location_table
from StartingItems import inventory, songs, equipment

__version__ = "5-2-4R.1.0"

# Parameters for generation
ALLOW_LOGIC = False # True for random logic, false otherwise
ALLOW_BRIDGETOKENS = True # Randomize Skulltula bridge condition
MAX_BRIDGE_TOKENS = 4 # Between 1 and 100
ALLOW_MASTERQUEST = False # Randomize master quest dungeons
ALLOW_DAMAGE_MULTIPLIER = True # Randomize damage multiplier
ALLOW_DERP = False # Randomize pointless things (textshuffle, unclear hints, etc)
ALLOW_RECENT_BROKEN = False # Section to hold settings currently broken

# Randomize starting inventory
# "off": No starting inventory
# "legacy": Randomly start with Tycoon's Wallet and Fast Travel (Farore's, Prelude, Serenade)
# "random": Randomize starting items, songs, and equipment up to the specified maximum for each category
STARTING_INVENTORY = "random"

# Maximum number of starting items, songs, and equipment for the "random" STARTING_INVENTORY setting
MAX_STARTING_ITEMS = 4 # Between 0 and 32
MAX_STARTING_SONGS = 2 # Between 0 and 12
MAX_STARTING_EQUIPMENT = 3 # Between 0 and 21

# Numbers of tricks and excluded locations to add
NUM_EXPECTED_TRICKS = 0
NUM_EXCLUDED_LOCATIONS = 0


# Populate random tricks using the constant above
def populate_tricks():
    weight = NUM_EXPECTED_TRICKS / len(logic_tricks)
    rand = 0
    tricks = []
    for _, v in logic_tricks.items():
        rand = random.random()
        if rand <= weight:
            tricks.append(v['name'])
        else:
            continue

    return tricks


# Populate random location exclusions using the constant above
def populate_location_exclusions():
    # prune the raw list of locations to only those that give items
    TYPES_NOT_INCLUDED = ['Event', 'Drop', 'Boss', 'GossipStone']
    refined_locations = []
    for k, v in location_table.items():
        if ((v[0] in TYPES_NOT_INCLUDED) or (v[0] == 'Shop' and k[-1] in ['1', '2', '3', '4'])):
            continue
        else:
            refined_locations.append(k)

    # randomly generate a list from the above for locations to exclude
    weight = NUM_EXCLUDED_LOCATIONS / len(refined_locations)
    excluded_locations = []
    r = 0
    for l in refined_locations:
        r = random.random()
        if r <= weight:
            excluded_locations.append(l)

    return excluded_locations


# Whether to start with Fast Travel
def start_with_fast_travel():
    if not hasattr(start_with_fast_travel, "choice"):
        start_with_fast_travel.choice = random.choice([True, False])

    return start_with_fast_travel.choice


# Whether to start with Tycoon's Wallet
def start_with_tycoons_wallet():
    if not hasattr(start_with_tycoons_wallet, "choice"):
        start_with_tycoons_wallet.choice = random.choice([True, False])

    return start_with_tycoons_wallet.choice


# Randomize starting pool up to the specified maximum
def populate_starting_pool(pool, max):
    k = random.randint(0, max)
    return random.sample(list(pool), k)


# Populate starting items
def populate_starting_items():
    if STARTING_INVENTORY == "legacy":
        starting_items = []
        if start_with_fast_travel():
            starting_items.append("farores_wind")
        if start_with_tycoons_wallet():
            starting_items.append("wallet")
            starting_items.append("wallet2")
            starting_items.append("wallet3")
        return starting_items
    elif STARTING_INVENTORY == "random":
        return populate_starting_pool(inventory, MAX_STARTING_ITEMS)
    else:
        return []


# Populate starting songs
def populate_starting_songs():
    if STARTING_INVENTORY == "legacy":
        starting_songs = []
        if start_with_fast_travel():
            starting_songs.append("prelude")
            starting_songs.append("serenade")
        return starting_songs
    elif STARTING_INVENTORY == "random":
        return populate_starting_pool(songs, MAX_STARTING_SONGS)
    else:
        return []


# Populate starting equipment
def populate_starting_equipment():
    if STARTING_INVENTORY == "legacy":
        return []
    elif STARTING_INVENTORY == "random":
        return populate_starting_pool(equipment, MAX_STARTING_EQUIPMENT)
    else:
        return []


def get_random_from_type(setting):
    if setting.gui_type == 'Checkbutton':
        return random.random() <= 0.5
    elif setting.gui_type == 'Combobox':
        s = list(setting.choices.keys())
        if setting.name == 'bridge' and not ALLOW_BRIDGETOKENS:
            s.pop(s.index('tokens'))
        return random.choice(s)
    elif setting.gui_type == 'Scale':
        s = list(setting.choices.keys())
        s.sort()
        return random.randint(s[0], s[-1])
    elif setting.gui_type == 'SearchBox':
        if setting.name == 'disabled_locations':
            return populate_location_exclusions()
        elif setting.name == 'allowed_tricks':
            return populate_tricks()
        elif setting.name == "starting_items":
            return populate_starting_items()
        elif setting.name == "starting_songs":
            return populate_starting_songs()
        elif setting.name == "starting_equipment":
            return populate_starting_equipment()
    else:
        return setting.default


def main():
    settings_to_randomize = list(get_settings_from_tab('main_tab'))[1:] + \
                list(get_settings_from_tab('detailed_tab')) + \
                list(get_settings_from_tab('other_tab')) + \
                list(get_settings_from_tab('starting_tab'))

    if not ALLOW_LOGIC:
        settings_to_randomize.pop(settings_to_randomize.index('logic_rules'))
    if not ALLOW_MASTERQUEST:
        settings_to_randomize.pop(settings_to_randomize.index('mq_dungeons_random'))
        settings_to_randomize.pop(settings_to_randomize.index('mq_dungeons'))
    if not ALLOW_DERP:
        settings_to_randomize.pop(settings_to_randomize.index('useful_cutscenes'))
        settings_to_randomize.pop(settings_to_randomize.index('fast_chests'))
        settings_to_randomize.pop(settings_to_randomize.index('logic_lens'))
        settings_to_randomize.pop(settings_to_randomize.index('ocarina_songs'))
        settings_to_randomize.pop(settings_to_randomize.index('clearer_hints'))
        settings_to_randomize.pop(settings_to_randomize.index('text_shuffle'))
        settings_to_randomize.pop(settings_to_randomize.index('hints'))
        settings_to_randomize.pop(settings_to_randomize.index('disabled_locations'))
        settings_to_randomize.pop(settings_to_randomize.index('allowed_tricks'))
        settings_to_randomize.pop(settings_to_randomize.index('one_item_per_dungeon'))
        settings_to_randomize.pop(settings_to_randomize.index('decouple_entrances'))
        settings_to_randomize.pop(settings_to_randomize.index('mix_entrance_pools'))
    if not ALLOW_RECENT_BROKEN:
        settings_to_randomize.pop(settings_to_randomize.index('shuffle_medigoron_carpet_salesman'))

    # Randomize the starting items
    if STARTING_INVENTORY == "off":
        settings_to_randomize.pop(settings_to_randomize.index('starting_equipment'))
        settings_to_randomize.pop(settings_to_randomize.index('starting_items'))
        settings_to_randomize.pop(settings_to_randomize.index('starting_songs'))

    # Draw the randomized settings
    random_settings = {}
    for info in setting_infos:
        if info.name in settings_to_randomize:
            random_settings[info.name] = get_random_from_type(info)
            print(info.name + ' : ' + info.gui_type + ' : ' + str(get_random_from_type(info)))

    # Choose the number of master quest dungeons using a geometric distribution (each dungeon has a 1/2**x chance)
    if ALLOW_MASTERQUEST:
        random_settings["mq_dungeons"] = sum([random.random() < 1/2**(x + 1) for x in range(12)])

    # Choose the number of starting hearts using a geometric distribution (each additional heart has a 1/2**x chance)
    random_settings["starting_hearts"] = 3 + sum([random.random() < 1/2**(x + 1) for x in range(17)])

    # Manually set the max number of skulls for bridge
    random_settings["bridge_tokens"] = random.randint(1, MAX_BRIDGE_TOKENS)

    # If damage multiplier quad or ohko, restrict ice traps
    if random_settings["damage_multiplier"] in ["quadruple", "ohko"] and \
        random_settings["junk_ice_traps"] in ['mayhem', 'onslaught'] :
        random_settings["junk_ice_traps"] = random.choice(["off", "normal", "on"])

    # Shuffle Triforce Hunt in with ganon's boss key and group LACS bk requirements
    bk_full = list(get_setting_info("shuffle_ganon_bosskey").choices.keys())
    bk_lacs_options = [entry for entry in bk_full if entry[:4] == 'lacs']
    bk_choice = random.choice([entry for entry in bk_full if not entry[:4] == 'lacs'] + ['th', 'lacs'])
    if bk_choice == 'th':
        random_settings['triforce_hunt'] = True
        random_settings['shuffle_ganon_bosskey'] = 'remove'
    elif bk_choice == 'lacs':
        random_settings['triforce_hunt'] = False
        random_settings['shuffle_ganon_bosskey'] = random.choice(bk_lacs_options)
    else:
        random_settings['triforce_hunt'] = False
        random_settings['shuffle_ganon_bosskey'] = bk_choice

    # Output the json file
    output = {'settings': random_settings}
    with open('rand-settings.json', 'w') as fp:
        json.dump(output, fp, indent=4)


if __name__ == '__main__':
    main()
