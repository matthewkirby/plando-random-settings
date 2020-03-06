import json
import random
from SettingsList import logic_tricks, setting_infos, get_settings_from_tab
from LocationList import location_table
from StartingItems import inventory, songs, equipment

__version__ = "5-1-73.1.4"

# Parameters for generation
ALLOW_LOGIC = False # True for random logic, false otherwise
ALLOW_ER = True # Randomize entrance randomizer settings
ALLOW_TRIHUNT = True # Randomize triforce hunt
ALLOW_BRIDGETOKENS = True # Randomize Skulltula bridge condition
MAX_BRIDGE_TOKENS = 4 # Between 1 and 100
ALLOW_MASTERQUEST = False # Randomize master quest dungeons
ALLOW_DAMAGE_MULTIPLIER = True # Randomize damage multiplier
ALLOW_DERP = False # Randomize pointless things (textshuffle, unclear hints, etc)

# Randomize starting inventory
# "off": No starting inventory
# "legacy": Randomly start with Tycoon's Wallet and Fast Travel (Farore's, Prelude, Serenade)
# "random": Randomize starting items, songs, and equipment up to the specified maximum for each category
STARTING_INVENTORY = "random"

# Maximum number of starting items, songs, and equipment for the "random" STARTING_INVENTORY setting
MAX_STARTING_ITEMS = 4 # Between 0 and 32
MAX_STARTING_SONGS = 2 # Between 0 and 12
MAX_STARTING_EQUIPMENT = 3 # Between 0 and 21

# MasterQuest specific options
NUM_MASTERQUEST = 0 # Overrides ALLOW_MASTERQUEST, max=12

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


settings_to_randomize = list(get_settings_from_tab('main_tab'))[1:] + \
            list(get_settings_from_tab('detailed_tab')) + \
            list(get_settings_from_tab('other_tab')) + \
            list(get_settings_from_tab('starting_tab'))

if not ALLOW_ER:
    settings_to_randomize.pop(settings_to_randomize.index('entrance_shuffle'))
if not ALLOW_LOGIC:
    settings_to_randomize.pop(settings_to_randomize.index('logic_rules'))
if not ALLOW_TRIHUNT:
    settings_to_randomize.pop(settings_to_randomize.index('triforce_hunt'))
if not ALLOW_MASTERQUEST or NUM_MASTERQUEST > 0:
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
    settings_to_randomize.pop(settings_to_randomize.index('all_reachable'))
if not ALLOW_DAMAGE_MULTIPLIER:
    settings_to_randomize.pop(settings_to_randomize.index('damage_multiplier'))

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

# Manually set the number of master quest dungeons
if NUM_MASTERQUEST > 0:
    random_settings["mq_dungeons"] = NUM_MASTERQUEST

# Manually set the max number of skulls for bridge
random_settings["bridge_tokens"] = random.randint(1, MAX_BRIDGE_TOKENS)

# Output the json file
output = {'settings': random_settings}
with open('rand-settings.json', 'w') as fp:
    json.dump(output, fp, indent=4)
