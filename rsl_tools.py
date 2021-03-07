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
    randomizer_settings = {
        "rom": os.path.join(rootdir, 'data','ZOOTDEC.z64'),
        "output_dir": os.path.join(rootdir, 'patches'),
        "compress_rom": "Patch", 
        "enable_distribution_file": "True",
        "distribution_file": os.path.join(rootdir, "data", "random_settings.json"),
        "create_spoiler": "True",
        "world_count": worldcount
    }

    with open(os.path.join('data', 'randomizer_settings.json'), 'w') as fp:
        json.dump(randomizer_settings, fp, indent=4)
    return randomizer_settings


def generate_patch_file(max_retries=3):
    retries = 0
    while(True):
        print(f"RSL GENERATOR: RUNNING THE RANDOMIZER - ATTEMPT {retries+1} OF {max_retries}")
        status_code = subprocess.call(
            [sys.executable, os.path.join("randomizer", "OoTRandomizer.py"), "--settings", os.path.join("..", "data", "randomizer_settings.json")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        if status_code != 0:
            retries += 1
            if retries < max_retries:
                continue
            print(f"RSL GENERATOR ERROR: MAX RETRIES ({max_retries}) REACHED. RESELECTING SETTINGS.")
            return 1
        break
    return 0
