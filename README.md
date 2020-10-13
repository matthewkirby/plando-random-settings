# PlandoRandomSettings
This script will generate a plando json file that can be fed into the Ocarina of Time randomzier with random values for each of the randomizer settings.
This script allows us to blindly randomize anything and (nearly) everything in the ranomizer, rather than just the natively supported random settings.

## Instructions
1. Download the dev-R branch of Ocarina of Time Randomizer. Version v5.2.65 R-6 or newer  (https://github.com/Roman971/OoT-Randomizer).
2. Navigate to the folder that contains `Gui.py` and make a new folder named `plando-random-settings`.
3. Place the contents of this repository in this new folder.
4. Run `PlandoRandomSettings.py` by either double clicking via the command line `$ python3 PlandoRandomSettings.py` to generate `blind_random_settings.json`.
5. Use this file as a plando file when you generate your randomizer seed.

## FAQ
#### When I double click `PlandoRandomSettings.py` nothing happens and no file is generated.

The script is crashing. Ensure that you have the correct version of dev-R Ocarina of Time randomizer and that the script is in the correct directory. If it is still not working, try to run via the command line to see the error message.

## To Do
- Write a test that prints all of the settings and options and compares them to what we expect. This can test if a new version of the rando has added new settings, options, or changed names