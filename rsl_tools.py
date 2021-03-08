import sys
import subprocess
import zipfile
import shutil
import os
import json
from version import randomizer_commit, randomizer_version
try: 
    import requests
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests



def download_randomizer():
    zippath = 'randomizer.zip'

    # Make sure an old zip isn't sitting around
    if os.path.isfile(zippath):
        os.remove(zippath)

    # Download the zipped randomizer
    r = requests.get(f'https://github.com/Roman971/OoT-Randomizer/archive/{randomizer_commit}.zip', stream=True)
    with open(zippath, 'wb') as fp:
        for chunk in r.iter_content():
            fp.write(chunk)
    
    # Extract the zip file and add __init__.py
    with zipfile.ZipFile(zippath, 'r') as zf:
        zf.extractall('.')
    os.rename(f'OoT-Randomizer-{randomizer_commit}', 'randomizer')
    with open(os.path.join('randomizer', '__init__.py'), 'w') as fp:
        pass

    # Delete the zip file
    os.remove(zippath)

def check_version():
    if os.path.isfile(os.path.join('randomizer', 'version.py')):
        from randomizer import version as ootrversion
        if ootrversion.__version__ == randomizer_version:
            return
        else:
            print("Updating the randomizer...")
            shutil.rmtree('randomizer')
            download_randomizer()
    else:
        print("Downloading the randomizer...")
        download_randomizer()
    return


# This function will take things from the GUI eventually.
def init_randomizer_settings(worldcount=1):
    rootdir = os.getcwd()

    with open('path_to_rom.txt', 'r') as fp:
        path_to_rom = fp.readline()

    randomizer_settings = {
        "rom": os.path.join(rootdir, path_to_rom),
        "output_dir": os.path.join(rootdir, 'patches'),
        "compress_rom": "Patch", 
        "enable_distribution_file": "True",
        "distribution_file": os.path.join(rootdir, "data", "random_settings.json"),
        "create_spoiler": "True",
        "world_count": worldcount
    }

    with open(os.path.join('data', 'randomizer_settings.json'), 'w') as fp:
        json.dump(randomizer_settings, fp, indent=4)


def generate_patch_file(max_retries=3):
    retries = 0
    while(True):
        print(f"RSL GENERATOR: RUNNING THE RANDOMIZER - ATTEMPT {retries+1} OF {max_retries}")
        completed_process = subprocess.run(
            [sys.executable, os.path.join("randomizer", "OoTRandomizer.py"), "--settings", os.path.join("..", "data", "randomizer_settings.json")],
            capture_output=True)

        if completed_process.returncode != 0:
            retries += 1
            if retries < max_retries:
                continue
            print(f"RSL GENERATOR: MAX RETRIES ({max_retries}) REACHED. RESELECTING SETTINGS.")
            break
        break
    return completed_process


# Compare weights file to settings list to check for changes to the randomizer settings table
def check_for_setting_changes(weights, randomizer_settings):
    for ele in ["bridge_tokens_max", "lacs_tokens_max", "triforce_goal_per_world_max"]:
        weights.pop(ele)

    # Find new or changed settings by name
    old_settings = list(set(weights.keys()) - set(randomizer_settings.keys()))
    new_settings = list(set(randomizer_settings.keys()) - set(weights.keys()))
    if len(old_settings) > 0:
        for setting in old_settings:
            print(f"{setting} with options {list(weights[setting].keys())} is no longer a setting.")
            weights.pop(setting)
        print("-------------------------------------")
    if len(new_settings) > 0:
        for setting in new_settings:
            print(f"{setting} with options {list(randomizer_settings[setting].keys())} is a new setting!")
        print("-------------------------------------")

    # Find new or changed options
    for setting in weights.keys():
        # Randomizer has appropriate types for each variable but we store options as strings
        randomizer_settings_strings = set(map(lambda x:x.lower(), map(str, list(randomizer_settings[setting].keys()))))
        old_options = list(set(weights[setting].keys()) - randomizer_settings_strings)
        new_options = list(randomizer_settings_strings - set(weights[setting].keys()))
        if len(old_options) > 0:
            for name in old_options:
                print(f"{setting} option {name} no longer exists.")
        if len(new_options) > 0:
            for name in new_options:
                print(f"{setting} option {name} is new!")
