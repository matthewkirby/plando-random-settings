""" Various functions needed to generate random settings seed that are not related
to the randomizer. """
import sys
import subprocess
import zipfile
import shutil
import os
import json
import glob
import stat
from version import randomizer_commit, randomizer_version
try:
    import requests
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
    import requests



def download_randomizer():
    """ Download the randomizer from commit listed in version.py """
    zippath = 'randomizer.zip'

    # Make sure an old zip isn't sitting around
    if os.path.isfile(zippath):
        os.remove(zippath)

    # Download the zipped randomizer
    req = requests.get(f'https://github.com/Roman971/OoT-Randomizer/archive/{randomizer_commit}.zip', stream=True)
    with open(zippath, 'wb') as fin:
        for chunk in req.iter_content():
            fin.write(chunk)

    # Extract the zip file and add __init__.py
    with zipfile.ZipFile(zippath, 'r') as zipped:
        zipped.extractall('.')
    shutil.move(f'OoT-Randomizer-{randomizer_commit}', 'randomizer')
    with open(os.path.join('randomizer', '__init__.py'), 'w') as fin:
        pass

    # Restore permissions in the unzipped randomizer
    for executable in [os.path.join('randomizer', 'OoTRandomizer.py'), os.path.join('randomizer', 'Decompress', 'Decompress')]:
        os.chmod(executable, os.stat(executable).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Delete the zip file
    os.remove(zippath)

def check_version():
    """ Ensure the downloaded version of the randomizer is the correct, if not update """
    if os.path.isfile(os.path.join('randomizer', 'version.py')):
        from randomizer import version as ootrversion
        if ootrversion.__version__ == randomizer_version:
            return
        print("Updating the randomizer...")
        shutil.rmtree('randomizer')
        download_randomizer()
    else:
        print("Downloading the randomizer...")
        download_randomizer()
    return

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
    ignore_list = ["tricks_list_msg", "bingosync_url"]

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
            if setting not in ignore_list:
                print(f"{setting} with options {list(randomizer_settings[setting].keys())} is a new setting!")
        print("-------------------------------------")

    # Find new or changed options
    for setting in weights.keys():
        # Randomizer has appropriate types for each variable but we store options as strings
        randomizer_settings_strings = set(map(lambda x: x.lower(), map(str, list(randomizer_settings[setting].keys()))))
        old_options = list(set(weights[setting].keys()) - randomizer_settings_strings)
        new_options = list(randomizer_settings_strings - set(weights[setting].keys()))
        if len(old_options) > 0:
            for name in old_options:
                print(f"{setting} option {name} no longer exists.")
        if len(new_options) > 0:
            for name in new_options:
                print(f"{setting} option {name} is new!")


class RandomizerError(Exception):
    """ A custom exception to specify that the randomizer is what threw the error. """
