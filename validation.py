from multiselects import ms_option_lookup
from randomizer.SettingsList import SettingInfos
import roll_settings as rs


def validate_rsl(weights):
    validate_weights(weights)
    validate_multiselect_knowledge()
    validate_conditionals()
    validate_overrides()


def validate_weights(weights):
    """ Function to check for new settings and options when the randomizer is updated. """
    # Settings to not care about validating if they show up in balanced weights because they are handled manually
    ignore_settings = ["custom_ice_trap_percent", "custom_ice_trap_count", "hint_dist"] + list(ms_option_lookup.keys())
    # Settings not to care about missing options (enumerations)
    ignore_options = ["special_deal_price_min", "special_deal_price_max"]

    randomizer_settings = rs.generate_balanced_weights(None)

    # Find new or changed settings by name
    print("Checking for new or removed settings...")
    rsl_settings_set = set(weights.keys())
    ootr_settings_set = set(randomizer_settings.keys())
    for setting in rsl_settings_set-ootr_settings_set:
        print(f"\tRSL:  {setting} {list(weights[setting].keys())}")
    for setting in ootr_settings_set-rsl_settings_set:
        if setting not in ignore_settings:
            print(f"\tOoTR: {setting} {list(SettingInfos.setting_infos[setting].choice_list)}")
    print("\n\n")

    # Find new or changed options
    print("Checking settings for new or removed options...")
    for setting, optweights in weights.items():
        if setting in ignore_settings:
            continue
        rsl_options = set(optweights.keys())
        ootr_options = set(map(lambda x: str(x).lower(), SettingInfos.setting_infos[setting].choice_list))
        for option in rsl_options-ootr_options:
            print(f"\tRSL:  {setting}:{option} removed or renamed")
        for option in ootr_options-rsl_options:
            if setting not in ignore_options:
                print(f"\tOoTR: {setting}:{option} newly added")
    print("\n\n")


def validate_multiselect_knowledge():
    print("Verifying multiselect knowledge...")
    for mskey in ms_option_lookup.keys():
        rslset = set(ms_option_lookup[mskey])
        ootrset = set(SettingInfos.setting_infos[mskey].choice_list)
        if rslset != ootrset:
            print(f"\t{mskey} mismatched!")
            print(f"\t\tRSL:  {rslset-ootrset}")
            print(f"\t\tOoTR: {ootrset-rslset}")
    print("\n\n")


def validate_overrides():
    pass


def validate_conditionals():
    pass