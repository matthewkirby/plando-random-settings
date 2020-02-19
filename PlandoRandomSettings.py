import json
import random
from SettingsList import logic_tricks, setting_infos, get_settings_from_tab
from LocationList import location_table
from StartingItems import inventory, songs, equipment

__version__ = "5-1-73.1.2"

# Parameters for generation
ALLOW_LOGIC = False # True for random logic, false otherwise
ALLOW_ER = True # Randomize entrance randomizer settings
ALLOW_TRIHUNT = True # Randomize triforce hunt
ALLOW_BRIDGETOKENS = True # Randomize Skulltula bridge condition
ALLOW_MASTERQUEST = False # Randomize master quest dungeons
ALLOW_DAMAGE_MULTIPLIER = True # Randomize damage multiplier
ALLOW_DERP = False # Randomize pointless things (textshuffle, unclear hints, etc)

# Randomize starting items
# "none": No starting items
# "legacy": Randomly start with Tycoon's Wallet and Fast Travel (Farore's, Prelude, Serenade)
# "everything": Randomize ALL starting items
STARTING_ITEMS = "everything"

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


# Populate starting pool (inventory, songs, equipment)
def populate_starting_pool(pool):
    starting_pool = []
    for item in pool:
        if random.random() < 0.05:
            starting_pool.append(pool[item].settingname)

    return starting_pool


# Populate starting inventory
def populate_starting_items():
    return populate_starting_pool(inventory)


# Populate starting songs
def populate_starting_songs():
    return populate_starting_pool(songs)


# Populate starting equipment
def populate_starting_equipment():
    return populate_starting_pool(equipment)


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
if STARTING_ITEMS in ["none", "legacy"]:
    settings_to_randomize.pop(settings_to_randomize.index('starting_equipment'))
    settings_to_randomize.pop(settings_to_randomize.index('starting_items'))
    settings_to_randomize.pop(settings_to_randomize.index('starting_songs'))

# Draw the randomized settings
random_settings = {}
for info in setting_infos:
    if info.name in settings_to_randomize:
        random_settings[info.name] = get_random_from_type(info)
        print(info.name + ' : ' + info.gui_type + ' : ' + str(get_random_from_type(info)))

# Randomize the starting items and songs in legacy mode
if STARTING_ITEMS == "legacy":
    starting_items = []
    starting_songs = []
    fast_travel = random.choice([True, False])
    omega_wallet = random.choice([True, False])
    if fast_travel:
        starting_items.append("farores_wind")
        starting_songs.append("prelude")
        starting_songs.append("serenade")
    if omega_wallet:
        starting_items.append("wallet")
        starting_items.append("wallet2")
        starting_items.append("wallet3")
    random_settings["starting_items"] = starting_items
    random_settings["starting_songs"] = starting_songs

# Manually set the number of master quest dungeons
if NUM_MASTERQUEST > 0:
    random_settings["mq_dungeons"] = NUM_MASTERQUEST

# Output the json file
output = {'settings': random_settings}
with open('rand-settings.json', 'w') as fp:
    json.dump(output, fp, indent=4)
