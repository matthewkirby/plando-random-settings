## Changelog

5.2.84 R-2 v1 - Skull Token, Skull Token
- For LACS and bridge medallions, stones and dungeons, we now have 50% chance for all to be required (6 meds, 3 stones, or 9 dungeon rewards) and 50% chance at variable (1-5 meds, 1-2 stones, 1-8 dungeons)
- Renamed `dungeons` option to `any_dungeon` for `shuffle_mapcompass`, `shuffle_smallkeys`, `shuffle_bosskeys` and `shuffle_ganon_bosskey`
- Added `lacs_tokens` as an option to `shuffle_ganon_bosskey`. Renormalized weights
    - Ganon BK in `any_dungeon` now possible as well
    - Even probability of: Triforce hunt, `remove`, `vanilla`, `dungeon`, Keysanity, LACS (dungeon rewards), and LACS Tokens
    - If Keysanity is chosen, even probability of `keysanity`, `overworld` or `any_dungeon`
    - If LACS (dungeon rewards) is chosen, even probability between `lacs_vanilla`, `lacs_medallion`, `lacs_stone` and `lacs_dungeons`
- `fast_bunny_hood` setting added and set to always on
- `shuffle_mapcompass` now includes `overworld` and `any_dungeon` and all of the options are equally weighted.
- Mask of truth hints are no longer broken, so hint requirements are now back to 12.5/12.5/75 MoT/SoA/Free
- New setting added `shuffle_fortresskeys` is plandod in `Conditionals.py` to have the same behavior as `shuffle_smallkeys`
- `lacs_tokens` is now drawn uniformally from 1-100 by the script (1-50 for co-op)

5.2.61 R-11 v2
- Added option for easy multiworld support, see README for instructions
- All errors are now dumped to ERRORLOG.TXT to help debug non-command line users

5.2.61 R-11 v1
- Bug fix for devR revisions greater than 10

5.2.65 R-6 v1 - Beans, Beans
- Shuffle Songs (Song Checks, Dungeon Rewards, Songsanity) 33/33/33 (was 50/50 SongChecks/Songsanity)
- Shuffle map/compass (overworld and dungeons options added). Both at zero weight for now (since the old options were not evenly distributed)
- Shuffle small keys (New overworld and dungeons options added). Even chance at remove/vanilla/dungeon/overworld/dungeonS/keysanity
- Shuffle Boss keys (New overworld and dungeons options added). Even chance at remove/vanilla/dungeon/overworld/dungeonS/keysanity
- Shuffle ganon boss key (new overworld and dungeons options added). Both at zero weight for now (since the old options were not evenly distributed).
- Hint dist tournament changed for S4 testing, tournament_S3 for previous tournament hint dist, bingo hint dist added. Bingo hints at weight of 0, all other even.

5.2.54 R-2 v1 - Mask of Truth, Mask of Truth
- Added a change log!
- Slight adjustment to hint requirements in weights file. Mask of Truth/Stone of Agony/free: 10/10/70 to 12.5/12.5/75
- Removed hints require Mask of Truth temporarily due to rando bug. We have moved the weighting to hints require Stone of Agony: 0/25/75
- Split version file off of the primary script to avoid users accidentally editing it
- Each version now also plandos the first two symbols of the seed hash. This can be used to know if the seed was generated with the correct version of this script.
- We explicitly check both the version of the randomizer and the version of the weights file to ensure that everything matches up. The rando must have the same major and minor versions and current or more recent fix number.