from multiselects import ms_option_lookup
from randomizer.SettingsList import SettingInfos


def validate_rsl(weights, randomizer_settings):
    validate_weights(weights, randomizer_settings)



def validate_weights(weights, randomizer_settings):
    """ Function to check for new settings and options when the randomizer is updated. """
    ignore_list = ["custom_ice_trap_percent", "custom_ice_trap_count", "bingosync_url", "starting_inventory",
        "tricks_list_msg", "empty_dungeons_count", "hint_dist", "plandomized_locations"] + list(ms_option_lookup.keys())
    # This second list is to avoid needing to specify every setting in enumerate fields. We still check that OUR keys exist, but not that we aren't missing any
    # special_deal_price_min for example supports 0, 5, 10, 15, ..., 990, 995 but I still want to ensure what we DO specify in weights is valid
    settings_ignore_list = ["special_deal_price_min", "special_deal_price_max"]

    # Find new or changed settings by name
    print("Checking for new or removed settings...")
    rsl_settings_set = set(weights.keys())
    ootr_settings_set = set(randomizer_settings.keys())
    for setting in rsl_settings_set-ootr_settings_set:
        print(f"\tRSL:  {setting} {list(weights[setting].keys())}")
    for setting in ootr_settings_set-rsl_settings_set:
        if setting not in ignore_list:
            print(f"\tOoTR: {setting} {list(SettingInfos.setting_infos[setting].choice_list)}")
    print("\n\n")

    # Find new or changed options
    print("Checking settings for new or removed options...")
    for setting in weights.keys():
        if setting in ignore_list:
            continue
        # Randomizer has appropriate types for each variable but we store options as strings
        randomizer_settings_strings = set(map(lambda x: x.lower(), map(str, list(randomizer_settings[setting].keys()))))
        old_options = list(set(weights[setting].keys()) - randomizer_settings_strings)
        new_options = list(randomizer_settings_strings - set(weights[setting].keys()))
        if len(old_options) > 0:
            for name in old_options:
                print(f"{setting} option {name} no longer exists.\n")
        if setting not in settings_ignore_list and len(new_options) > 0:
            for name in new_options:
                print(f"{setting} option {name} is new!\n")
    print("\n\n")

    print("Verifying multiselect knowledge...")
    for mskey in ms_option_lookup.keys():
        rslset = set(ms_option_lookup[mskey])
        ootrset = set(SettingInfos.setting_infos[mskey].choice_list)
        if rslset != ootrset:
            print(f"\t{mskey} mismatched!")
            print(f"\t\tRSL:  {rslset-ootrset}")
            print(f"\t\tOoTR: {ootrset-rslset}")
    print("\n\n")
