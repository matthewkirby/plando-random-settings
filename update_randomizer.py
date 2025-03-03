import os
import sys
import stat
import zipfile
import shutil
import subprocess
from utils import cleanup
import rslversion as rslv


def check_python():
    if sys.version_info < rslv.MIN_PY_VERSION:
        print(f"Error: Python {rslv.MIN_PY_VERSION[0]}.{rslv.MIN_PY_VERSION[1]} or higher is required to run this script.")
        sys.exit(1)

def check_version():
    """ Ensure the downloaded version of the randomizer is the correct, if not update """
    if os.path.isfile(os.path.join('randomizer', 'version.py')):
        from randomizer import version as ootrversion
        if ootrversion.__version__ == rslv.randomizer_version:
            return
        print("Updating the randomizer...")
        shutil.rmtree('randomizer')
        download_randomizer()
    else:
        print("Downloading the randomizer...")
        download_randomizer()
    return


def download_randomizer():
    """ Download the randomizer from commit listed in version.py """

    try:
        import requests
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'requests'])
        import requests

    zippath = 'randomizer.zip'

    # Make sure an old zip isn't sitting around
    cleanup(zippath)

    # Download the zipped randomizer
    req = requests.get(f'https://github.com/{rslv.randomizer_repo}/archive/{rslv.randomizer_commit}.zip', stream=True)
    with open(zippath, 'wb') as fin:
        for chunk in req.iter_content():
            fin.write(chunk)

    # Extract the zip file and add __init__.py
    with zipfile.ZipFile(zippath, 'r') as zipped:
        zipped.extractall('.')
    shutil.move(f'OoT-Randomizer-{rslv.randomizer_commit}', 'randomizer')
    with open(os.path.join('randomizer', '__init__.py'), 'w') as fin:
        pass

    # Restore permissions in the unzipped randomizer
    for executable in [
        os.path.join('randomizer', 'OoTRandomizer.py'),
        os.path.join('randomizer', 'bin', 'Decompress', 'Decompress'),
        os.path.join('randomizer', 'bin', 'Decompress', 'Decompress_ARM32'),
        os.path.join('randomizer', 'bin', 'Decompress', 'Decompress_ARM64'),
        os.path.join('randomizer', 'bin', 'Decompress', 'Decompress.out'),
        os.path.join('randomizer', 'bin', 'Decompress', 'Decompress_ARM64.out'),
    ]:
        os.chmod(executable, os.stat(executable).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Delete the zip file
    cleanup(zippath)
