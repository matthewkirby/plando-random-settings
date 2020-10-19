## Changelog

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