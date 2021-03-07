# Random Settings Generator
This script will generate a patch file for The Legend of Zelda Ocarina of Time Randomizer with randomly selected randomizer settings.
This script allows its user to randomize every setting in the Randomizer, not just settings that are natively supported to be randomized.

## Instructions
1. Have Python 3.7 (or newer) installed. This is also a requirement of the randomizer.
2. Download the zip file of the source code from the release page and unzip anywhere: https://github.com/matthewkirby/plando-random-settings/releases
3. Run the code by double clicking `RandomSettingsGenerator.py` or running `python3 RandomSettingsGenerator.py` via the command line.

## Multiworld/Dungeon Door Requirement (DDR)
- If you are playing a format besides an official Random Setting League race, you may wish to edit the weights. We also provide presets for multiworld and the DDR ruleset at the moment. To use these presets, open `RandomSettingsGenerator.py` in a text editor and remove the `# ` (including the space after the `#`) from line 16 for multiworld or from line 17 for DDR.

## Command Line Interface Options
If you opt to run the script via the command line, you have several options available to you
- `--no_seed`: Generates a plando file in the `data` directory but does not generate a patch file
- `--override <path_to_weights_file>`: Provide a weights override file to be used on top of the default RSL weights. Random settings will be generated using the weights in the override file. Any settings not in the override file will get their weights from the RSL weights. The file is expected to be in the weights directory at the moment.
- `--worldcount <integer>`: The number of worlds to generate for generating multiworld patch files. If this is not given, the default is 1.

# FAQ
> Do I need to download the randomizer?
Not anymore! Since this code doesn't function without the randomizer and having the wrong version will crash the code, we now manage that for you! This code base is all you will need to get started! Once you have your patch file you can patch with any version of the randomizer you have downloaded, the one we download in the `randomizer` directory or the web generator at https://ootrandomizer.com/