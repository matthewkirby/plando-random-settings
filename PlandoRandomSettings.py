from SettingsList import logic_tricks, setting_infos, get_settings_from_tab
from LocationList import location_table
import json
import sys
import random as R

__version__ = 5.1.73

# Parameters for generation
ALLOW_LOGIC = False # True for random logic, false otherwise
ALLOW_ER = True # Randomize entrance randomizer settings
ALLOW_TRIHUNT = True # Randomize triforce hunt
ALLOW_BRIDGETOKENS = True # Randomize Skulltula bridge condition
ALLOW_MASTERQUEST = False # Randomize master question dungeons
ALLOW_DAMAGE_MULTIPLIER = True # Randomize damage multiplier
ALLOW_DERP = False # Randomize pointless things (textshuffle, unclear hints, etc)

# Randomize starting items
# "none": No starting items
# "legacy": Randomly start with Tycoon's Wallet and Fast Travel (Faore, Prelude, Serenade)
# "full": Randomize ALL starting items (not implemented)
STARTING_ITEMS = "legacy" # Randomize starting items

# MasterQuest specific options
NUM_MASTERQUEST = 0 # Overrides ALLOW_MASTERQUEST, max=12

# Numbers of tricks and excluded locations to add
NUM_EXPECTED_TRICKS = 0
NUM_EXCLUDED_LOCATIONS = 0


# Populate random tricks using the constant above
def populateTricks():
    weight = NUM_EXPECTED_TRICKS / len(logic_tricks)
    r = 0
    tricks = []
    for k,v in logic_tricks.items():
        r = R.random()  
        if r <= weight:
            tricks.append(v['name'])
        else:
            continue

    return tricks

# Populate random location exclusions using the constant above
def populateLocationExclusions():
    # prune the raw list of locations to only those that give items
    TYPES_NOT_INCLUDED = ['Event', 'Drop', 'Boss', 'GossipStone']
    refined_locations = []
    for k,v in location_table.items():
        if ((v[0] in TYPES_NOT_INCLUDED) or (v[0] == 'Shop' and k[-1] in ['1','2','3','4'])):
            continue
        else:
            refined_locations.append(k)
    
    # randomly generate a list from the above for locations to exclude
    weight = NUM_EXCLUDED_LOCATIONS / len(refined_locations)
    excluded_locations = []
    r = 0
    for l in refined_locations:
        r = R.random()
        if r <= weight:
            excluded_locations.append(l)
    
    return excluded_locations

def getRandomFromType(setting):
    if setting.gui_type == 'Checkbutton':
        return R.random() <= 0.5
    elif setting.gui_type == 'Combobox':
        s = list(setting.choices.keys())
        if setting.name == 'bridge' and not ALLOW_BRIDGETOKENS:
            s.pop(s.index('tokens'))
        return R.choice(s)
    elif setting.gui_type == 'Scale':
        s = list(setting.choices.keys())
        s.sort()
        return R.randint(s[0], s[-1])
    elif setting.gui_type == 'SearchBox':
        if setting.name == 'disabled_locations':
            return populateLocationExclusions()
        elif setting.name == 'allowed_tricks':
            return populateTricks()
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
        random_settings[info.name] = getRandomFromType(info)
        print(info.name + ' : ' + info.gui_type + ' : ' + str(getRandomFromType(info)))

# Randomize the starting items
if STARTING_ITEMS == "legacy":
    starting_items_dict = {}
    fast_travel = R.choice([True, False])
    omega_wallet = R.choice([True, False])
    if fast_travel:
        starting_items_dict.update({"Farores Wind": 1, "Prelude of Light": 1, 
                                    "Serenade of Water": 1})
    if omega_wallet:
        starting_items_dict.update({"Progressive Wallet": 3})
    random_settings["starting_items"] = starting_items_dict


# Manually set the number of master quest dungeons
if NUM_MASTERQUEST > 0:
    random_settings["mq_dungeons"] = NUM_MASTERQUEST

# Output the json file
output = {'settings': random_settings}
with open('rand-settings.json', 'w') as fp:
    json.dump(output, fp, indent=4)
