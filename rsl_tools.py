""" Various functions needed to generate random settings seed that are not related
to the randomizer. """
import sys
import subprocess
import os
import json
import glob
sys.path.append("randomizer")
# from randomizer.SettingsList import get_setting_info
from randomizer.SettingsList import SettingInfos
from multiselects import ms_option_lookup


def randomizer_settings_func(rootdir=os.getcwd(), plando_filename='random_settings.json', worldcount=1):
    """ Set the base randomizer settings. This function is a placeholder for a future GUI """
    return {
        "rom": find_rom_file(),
        "output_dir": os.path.join(rootdir, 'patches'),
        "compress_rom": "Patch",
        "enable_distribution_file": "True",
        "distribution_file": os.path.join(rootdir, "data", plando_filename),
        "create_spoiler": "True",
        "world_count": worldcount
    }


def init_randomizer_settings(plando_filename='random_settings.json', worldcount=1):
    """ Save the randomizer settings to a file. """
    settings = randomizer_settings_func(plando_filename=plando_filename, worldcount=worldcount)

    with open(os.path.join('data', 'randomizer_settings.json'), 'w') as fout:
        json.dump(settings, fout, indent=4)


def generate_patch_file(plando_filename='random_settings.json', worldcount=1, max_retries=3):
    """ Using the randomized settings, roll a seed using the randomizer CLI. """
    settings = json.dumps(randomizer_settings_func(plando_filename=plando_filename, worldcount=worldcount))

    retries = 0
    while True:
        print(f"RSL GENERATOR: RUNNING THE RANDOMIZER - ATTEMPT {retries+1} OF {max_retries}")
        completed_process = subprocess.run(
            [sys.executable, os.path.join("randomizer", "OoTRandomizer.py"), "--settings=-"],
            capture_output=True,
            input=settings,
            encoding='utf-8',
        )

        if completed_process.returncode != 0:
            retries += 1
            if retries < max_retries:
                continue
            print(f"RSL GENERATOR: MAX RETRIES ({max_retries}) REACHED. RESELECTING SETTINGS.")
            break
        break
    return completed_process


# This function will probably need some more meat to it. If the user is patching the z64 file in the same directory it will find that
def find_rom_file():
    """ Find the Ocarina of Time rom file stored by the user in this directory. """
    rom_extensions = ["*.n64", "*.N64", "*.z64", "*.Z64"]
    for ext in rom_extensions:
        rom_filename = glob.glob(os.path.join(os.getcwd(), "**", ext), recursive=True)
        if len(rom_filename) > 0:
            break

    # No rom file found
    if len(rom_filename) == 0:
        raise FileNotFoundError("RSL GENERATOR ERROR: NO .n64 or .z64 ROM FILE FOUND.")
    return rom_filename[0]


# Compare weights file to settings list to check for changes to the randomizer settings table
def check_for_setting_changes(weights, randomizer_settings):
    """ Function to check for new settings and options when the randomizer is updated. """
    ignore_list = ["custom_ice_trap_percent", "custom_ice_trap_count", "bingosync_url", "starting_inventory",
        "tricks_list_msg", "empty_dungeons_count", "hint_dist"] + list(ms_option_lookup.keys())

    # Find new or changed settings by name
    old_settings = list(set(weights.keys()) - set(randomizer_settings.keys()))
    new_settings = list(set(randomizer_settings.keys()) - set(weights.keys()))
    if len(old_settings) > 0:
        for setting in old_settings:
            print(f"{setting} with options {list(weights[setting].keys())} is no longer a setting.\n")
            weights.pop(setting)
        print("-------------------------------------")
    if len(new_settings) > 0:
        for setting in new_settings:
            if setting not in ignore_list:
                print(f"{setting} with options {list(randomizer_settings[setting].keys())} is a new setting!\n")
        print("-------------------------------------")

    # Find new or changed options
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
        if len(new_options) > 0:
            for name in new_options:
                print(f"{setting} option {name} is new!\n")


def benchmark_weights(weight_options, weight_dict, weight_multiselect):
    """ Compare weights file definition to empirical data from generated spoiler logs. """
    # Initialize weight comparison object
    settings_counts = {}
    geometric_multis = []
    for setting_name, setting_options in weight_dict.items():
        # custom distros used for woth/goal split, which makes it difficult to directly detect the distro in spoilers
        if setting_name != 'hint_dist':
            settings_counts[setting_name] = {"disabled_seeds": 0}
            option_total = 0
            for setting_option, option_weight in setting_options.items():
                settings_counts[setting_name][setting_option] = {
                    "weight": option_weight,
                    "total_seeds": 0,
                    "normalized_weight": 0,
                    "fraction_seeds": 0
                }
                option_total += option_weight
            # Special case for skull and heart conditionals
            conditional_mod = 0
            if "conditionals" in weight_options and setting_name in ['bridge', 'shuffle_ganon_bosskey']:
                dynamic_options = ["tokens", "hearts"]
                for dynamic_conditional in ["dynamic_skulltula_wincon", "dynamic_heart_wincon"]:
                    if dynamic_conditional in weight_options["conditionals"]:
                        if weight_options["conditionals"][dynamic_conditional][0]:
                            global_chance = weight_options["conditionals"][dynamic_conditional][1]
                            split_chance = weight_options["conditionals"][dynamic_conditional][2].split("/")
                            split_type = ['bridge', 'shuffle_ganon_bosskey'].index(setting_name)
                            option_name = dynamic_options[["dynamic_skulltula_wincon", "dynamic_heart_wincon"].index(dynamic_conditional)]
                            option_chance = global_chance/100 * int(split_chance[split_type])/100 + global_chance/100 * int(split_chance[2])/100
                            settings_counts[setting_name][option_name]["weight"] = "dynamic"
                            settings_counts[setting_name][option_name]["normalized_weight"] = option_chance
                            conditional_mod += option_chance

            for setting_option, option_weight in setting_options.items():
                if settings_counts[setting_name][setting_option]["normalized_weight"] == 0:
                    settings_counts[setting_name][setting_option]["normalized_weight"] = float(option_weight / option_total * (1 - conditional_mod))
    for setting_name, multi_options in weight_multiselect.items():
        settings_counts[setting_name] = {"disabled_seeds": 0}
        if not multi_options["geometric"]:
            for setting_option, option_pct in multi_options["opt_percentage"].items():
                settings_counts[setting_name][setting_option] = {
                    "weight": str(option_pct) + "% (global " + str(multi_options["global_enable_percentage"]) + "%)",
                    "total_seeds": 0,
                    "normalized_weight": float(option_pct / 100 * multi_options["global_enable_percentage"] / 100),
                    "fraction_seeds": 0
                }
        else:
            geometric_multis.append(setting_name)
            max_options = len(SettingInfos.setting_infos[setting_name].choices)
            for option_num in range(0, max_options+1):
                settings_counts[setting_name][option_num] = {
                    "weight": str(2**(max_options - option_num)) + " (global " + str(multi_options["global_enable_percentage"]) + "%)",
                    "total_seeds": 0,
                    "normalized_weight": float((50.0/2**option_num) / 100 * multi_options["global_enable_percentage"] / 100),
                    "fraction_seeds": 0
                }

    # Count instances of each setting option in pre-rolled seeds.
    # Use the --stress_test option to bulk generate seeds.
    print("Processing spoilers")
    fcount = 0
    ftotal = len(glob.glob(os.path.join("patches", "*_Spoiler.json")))
    for filename in glob.glob(os.path.join("patches", "*_Spoiler.json")):
        fcount = fcount + 1
        afile = filename.split("_")
        settings_hash = afile[1]
        seed = afile[2]
        sys.stdout.write("\r%d / %d: %s   " % (fcount, ftotal, (settings_hash + "_" + seed)))
        with open(filename) as sp_file:
            sp = json.load(sp_file)
            for setting_name, option_value in sp["settings"].items():
                if isinstance(option_value, list):
                    setting_option = option_value
                elif not isinstance(option_value, str):
                    setting_option = str(option_value)
                else:
                    setting_option = option_value
                if isinstance(option_value, bool):
                    setting_option = setting_option.lower()
                if setting_name in settings_counts.keys() and setting_name not in geometric_multis:
                    if isinstance(setting_option, list):
                        for o in setting_option:
                            settings_counts[setting_name][o]["total_seeds"] += 1
                    else:
                        settings_counts[setting_name][setting_option]["total_seeds"] += 1
                if setting_name in settings_counts.keys() and setting_name in geometric_multis:
                    settings_counts[setting_name][len(setting_option)]["total_seeds"] += 1
            # If the setting is disabled, it won't be in the spoiler log and skews the seed fraction.
            for setting_name in settings_counts.keys():
                if setting_name not in sp["settings"].keys():
                    settings_counts[setting_name]["disabled_seeds"] += 1
    for setting_name, setting_options in settings_counts.items():
        for setting_option, option_data in setting_options.items():
            if setting_option != 'disabled_seeds':
                if ftotal != settings_counts[setting_name]["disabled_seeds"]:
                    settings_counts[setting_name][setting_option]["fraction_seeds"] = float(option_data["total_seeds"] / (ftotal - settings_counts[setting_name]["disabled_seeds"]))

    # Create report
    print("\nExporting weights report")
    report = '<!DOCTYPE html><html><head><style>body {font-family: sans-serif;} .setting_container {border-bottom: 1px solid #666; padding: 24px;} .setting_name {font-size: 1.5em; font-weight: bold; margin: 8px 0px} .option_error {background-color: red; color: white;} .option_alert {background-color: yellow;} .setting_disabled {color: #AAA;} .option_row td {padding-right: 16px;} .option_header {font-weight: bold;}</style></head><body><h1>Random Settings Weights Verification</h1>'
    report += '<div class="option_alert">Yellow options deviate from weights by >10%</div>'
    report += '<div class="option_error">Red options are not found in any seed despite non-zero weight</div>'
    report += '<div class="setting_disabled">Grayed-out options are not found in any seeds, likely disabled by another setting</div>'
    for setting_name, setting_options in settings_counts.items():
        setting_class = "setting_container"
        if settings_counts[setting_name]["disabled_seeds"] == ftotal:
            setting_class += " setting_disabled"
        report += '<div class="'+setting_class+'"><div class="setting_name">'+setting_name+'</div><table class="setting_options">'
        report += '<tr class="option_row option_header">' + \
                  '<td>Option</td>' + \
                  '<td>Weight</td>' + \
                  '<td>Total Seeds</td>' + \
                  '<td>Normalized Weight</td>' + \
                  '<td>Fraction Seeds</td>' + \
                  '</tr>'
        for setting_option, option_data in setting_options.items():
            if setting_option != 'disabled_seeds':
                option_class = "option_row"
                if option_data["total_seeds"] == 0 and option_data["normalized_weight"] != 0 and settings_counts[setting_name]["disabled_seeds"] != ftotal:
                    option_class += " option_error"
                if (abs(option_data["fraction_seeds"] - option_data["normalized_weight"]) > option_data["normalized_weight"] / 10 and
                option_data["normalized_weight"] != 0 and option_data["total_seeds"] != 0):
                    option_class += " option_alert"
                report += '<tr class="'+str(option_class)+'">' + \
                        '<td>'+str(setting_option)+'</td>' + \
                        '<td>'+str(option_data["weight"])+'</td>' + \
                        '<td>'+str(option_data["total_seeds"])+'</td>' + \
                        '<td>'+str(option_data["normalized_weight"])+'</td>' + \
                        '<td>'+str(option_data["fraction_seeds"])+'</td>' + \
                        '</tr>'
        report += '</table></div>'
    report += "</body></html>"
    with open("weights_report.html", "w") as report_file:
        report_file.writelines(report)
    sys.stdout.write("Report created as %s" % (os.path.abspath("weights_report.html")))


class RandomizerError(Exception):
    """ A custom exception to specify that the randomizer is what threw the error. """
