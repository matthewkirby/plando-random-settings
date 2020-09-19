## Changelog

5.2.54 R-2 v1 - Mask of Truth, Mask of Truth
- Added a change log!
- Slight adjustment to hint requirements in weights file. Mask of Truth/Stone of Agony/free: 10/10/70 to 12.5/12.5/75
- Removed hints require Mask of Truth temporarily due to rando bug. We have moved the weighting to hints require Stone of Agony: 0/25/75
- Split version file off of the primary script to avoid users accidentally editing it
- Each version now also plandos the first two symbols of the seed hash. This can be used to know if the seed was generated with the correct version of this script.
- We explicitly check both the version of the randomizer and the version of the weights file to ensure that everything matches up. The rando must have the same major and minor versions and current or more recent fix number.