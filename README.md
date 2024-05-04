# Random Settings Generator
This is a generator for a randomized seed of The Legend of Zelda Ocarina of Time Randomizer with randomly generated settings.
The base functionality of the randomizer allows you to randomize many of the settings but this script builds upon that.

1. Any setting can be randomized whereas the base randomizer restricts this functionality to "main settings".
2. A weights file can be used for control over the generation. This allows you to select settings not to randomize, select which of a setting's options you would like to randomize, and control the relative weights of each setting's options.
3. The selected settings are hidden by default so no players know what settings were chosen until they discover it in game.

The above functionality requires this external generator to run, but this code also downloads and maintains the proper version of the randomizer so you still get a patch file out like normal.


# Instructions
Requirements: Python 3.9 (or newer)

1. Download the latest [release](https://github.com/matthewkirby/plando-random-settings/releases) and unzip the folder anywhere.
2. Place your Ocarina of Time 1.0 rom in this directory. It must have the `.z64` file extension. If your rom has a different file extension or is a later version of the game, you can use [this tool](https://oot.flagrama.com/) to convert to the required version.
3. Run `RandomSettingsGenerator.py`. This can be done by double-clicking the file or running the script via the command line `python3 RandomSettingsGenerator.py`.
4. After it finishes running, your patch file will be saved in the `patches` directory.


# Advanced Instructions
```console
$ pip install virtualenv
$ sudo add-apt-repository ppa:deadsnakes/ppa
$ sudo apt install python3.9 && sudo apt install python3.9-distutils
$ virtualenv -p python3.9 venv
$ source venv/bin/activate
$ pip install requests
$ python RandomSettingsGenerator.py
```


# Rolling seeds with Weight Overrides
If you are playing a format besides an official Random Setting League race, you may wish to edit the weights.

1. Put the weights you wish to change into a JSON file in the weights folder
2. Open `RandomSettingsGenerator.py` in a text editor and add the line `global_override_fname = "<override file name>.json"` where you replace `<override file name>` with the name of your weights file.


# Command Line Interface Usage
The following are available via the command line interface
- `--no_seed`: Generates an Ocarina of Time Randomizer plandomizer file in the `data` directory but does not generate a patch file.
- `--override <path_to_weights_file>`: Provide a weights override file to be used on top of the default RSL weights. Any settings not in the override file will get their weights from the RSL weights.
- `--worldcount <integer>`: Generate a randomizer multiworld seed with the given number of worlds.
- `--check_new_settings`: Compare the full list of settings and options available in the randomizer to what is included in the weights file. Any settings or options that are missing from the weights file or are in the weights file but not in the randomizer settings are reported. This is primarily used when the randomizer version is updated to ensure that we don't miss a setting or option that was changed.
- `--no_log_errors`: If an error occurs, do not create `ERRORLOG.txt`. They will still be printed to the console.
- `--stress_test <integer>`: Sequentially generate many seeds for benchmarking.
- `--benchmark`: Compare the weights file to the spoiler log data. This should be run after `--stress_test`.
- `--plando_retries <integer>`: The retry limit for generating a plandomizer file. Default 5.
- `--rando_retries <integer>`: The retry limit for running the randomizer with a given settings plandomizer file. Default 3.


# Conditionals
There are several functions available in weights file to allow finer control over combinations of settings. You can turn each of these on or off as well as change their options in the weights file. In the weights file under `options` and then `conditionals`, simply provide a json object where the key is the name of the conditional and the value is a list of its parameters. The first parameter is always the status, `true` or `false` to turn it on or off. To see an example of how this looks, see the [current RSL weights file](https://github.com/matthewkirby/plando-random-settings/blob/master/weights/rsl_season6.json#L12).

### `constant_triforce_hunt_extras: [status]`
When enabled, ensure that the item pool always has 25\% extra Triforce pieces for Triforce Hunt.

### `exclude_minimal_triforce_hunt: [status]`
When enabled, if Triforce Hunt is enabled, prevent the `item_pool` setting from having the `minimal` option.

### `exclude_ice_trap_misery: [status]`
When enabled, if the damage multiplier is quadruple damage or one hit ko, prevent ice trap onslaught and ice trap mayhem.

### `disable_pot_chest_texture_independence: [status]`
When enabled, match `correct_chest_appearances` and `correct_potcrate_appearances`.

### `disable_keysanity_independence: [status]`
When enabled, match the `shuffle_hideoutkeys` and `shuffle_tcgkeys` settings to the selected option for `shuffle_smallkeys`.

### `restrict_one_entrance_randomizer: [status]`
When enabled, ensure that no more than one entrance pool is shuffled.

### `random_scrubs_start_wallet: [status]`
When enabled, add a wallet to the starting items if the deku scrubs prices are set to `random`.

### `dynamic_skulltula_wincon: [status, active%, "bridge%/gbk%/both%"]`
When enabled, roll the chance for a Golden Skulltula Token win conditional separately.
- `active%`: integer from 0 to 100. If this conditional is enabled, the chance to use it.
- `"bridge%/gbk%/both%"`: Chances for the skulltula win condition to be the bridge, the Ganon boss key, or both. These should be a string with three numbers separated by `/`. For example `"40/40/20"` would be a 40% chance for the bridge condition, a 40% chance for the Ganon boss key, and a 20% chance for both.

### `dynamic_heart_wincon: [status, active%, "bridge%/gbk%/both%"]`
When enabled, roll the chance for a heart win conditional separately.
- `active%`: integer from 0 to 100. If this conditional is enabled, the chance to use it.
- `"bridge%/gbk%/both%"`: Chances for the heart win condition to be the bridge, the Ganon boss key, or both. These should be a string with three numbers separated by `/`. For example `"40/40/20"` would be a 40% chance for the bridge condition, a 40% chance for the Ganon boss key, and a 20% chance for both.

### `split_collectible_bridge_conditions: [status, active%, "heart%/token%", "bridge%/gbk%/both%"]`
When enabled, combine the functionality of `dynamic_skulltula_wincon` and `dynamic_heart_wincon` while preventing a seed from generating with a skulltula bridge and heart ganon boss key (or vice versa).
- `active%`: integer from 0 to 100. If this conditional is enabled, the chance to use it.
- `"heart%/token%"`: If enabled and active, the chances for hearts to be chosen vs tokens to be chosen.
- `"bridge%/gbk%/both%"`: Whether the collectible condition should be on the bridge condition, the Ganon boss key, or both.

### `shuffle_goal_hints: [status, active%]`
When enabled, swap Way of the Hero hints to the Goal hint type.
- `active%`: integer from 0 to 100. If this conditional is enabled, the chance to use it.

### `replace_dampe_diary_hint_with_lightarrow: [status]`
The diary in Dampe's hut as an adult tells you the location of the hookshot in vanilla. The randomizer has a miscellaneous hint that can be enabled to update this text to the location of a hookshot. When this conditional is enabled, the diary hint is overridden to tell you the location of the light arrows. This is useful as the Ganondorf light arrow hint is usually locked behind the Ganon's Castle trials.

### `adjust_chaos_hint_distro: [status]`
Make the following adjustments to the randomizer's default Chaos hint distribution
- Ensure every `always` hint appears on two gossip stones in game.
- Remove duplicate `sometimes` hint categories (`overworld`, `dungeon`, `songs`) since every `sometimes` hint falls into at least one of these categories.

### `exclude_mapcompass_info_remove: [status]`
If `enhance_map_compass` is enabled, ensure that the maps and compasses exist in the game and are not simply removed.

### `ohko_starts_with_nayrus: [status]`
When the one hit ko damage multiplier is enabled, start the player with Nayru's Love.

### `invert_dungeons_mq_count: [status, active%]`
Swap the behavior for vanilla and Master Quest dungeons. This set every dungeon to their Master Quest variant and then use the various methods defined in the script to determine how many of those should be changed back to vanilla.
- `active%`: integer from 0 to 100. If this conditional is enabled, the chance to use it.

### `replicate_old_child_trade: [status]`
Emulate the old behavior for the child trade quest. This will randomly chose one of three things
- 25%: Child trade quest is disabled. Begin the vanilla trade quest by speaking with Malon outside of Hyrule Castle for the Weird Egg.
- 25% Child trade quest is disabled EXCEPT the Weird Egg check. Speaking with Malon outside of Hyrule Castle will give you a randomized item.
- 50% Child trade quest is disabled EXCEPT start with Zelda's Letter. Both Talon and Malon are already back in Lon Lon Ranch and you start with the item on the Zelda's Lullaby check.

### `shuffle_valley_lake_exit: [status]`
If both overworld entrance randomizer and owl shuffle are on, shuffle the Gerudo Valley to Lake Hylia water entrance into the pool.

### `select_one_pots_crates_freestanding: [status, active%, "pots%/crates%/freestanding%", "overworld%/dungeon%/all%"]`
When enabled, randomly chose to shuffle one of pots, crates, or freestanding rupees/hearts as well as if they should be shuffled in overworld, dungeons, or everywhere.
- `active%`: integer from 0 to 100. If this conditional is enabled, the chance to use it.
- `"pots%/crates%/freestanding%"`: Chance to select pots/crates/freestanding setting. Should be formatted like `"33/33/33"`.
- `"overworld%/dungeon%/all%"`: For the previously selected setting, chance to shuffle the locations in the overworld, dungeons, or everywhere. Should be formatted like `"33/33/33"`.


# FAQ
> When I double click `RandomSettingsGenerator.py` it instantly opens a little window and then closes and there are no files in the `patches` folder.

This means that the code crashed for some reason. Usually this is because you forgot to put your rom file in the folder. Check for a file called `ERRORLOG.TXT`. Any errors that occur will be saved there. If you cannot figure out what went wrong, head over to the Ocarina of Time Randomizer discord channel (https://discord.gg/ootrandomizer) and ask for help in the #rsl-discussion text channel.

> It didn't work! What do I do?

If you are running the code on the command line, the error message should be displayed. If you are double clicking the script, a file `ERRORLOG.TXT` should have been generated and the error message is saved there. If you cannot figure out what went wrong, head over to the Ocarina of Time Randomizer discord channel (https://discord.gg/ootrandomizer) and ask for help in the #rsl-discussion text channel.

> Do I need to download the randomizer?

Not anymore! Since this code doesn't function without the randomizer and having the wrong version will crash the code, we now manage that for you! This code base is all you will need to get started! Once you have your patch file you can patch with any version of the randomizer you have downloaded, the one we download in the `randomizer` directory or the web generator at https://ootrandomizer.com/