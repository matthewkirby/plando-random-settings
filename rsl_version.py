__version__ = "5.2.117 R-1 v1"
version_hash_1 = "Bottled Milk"
version_hash_2 = "Bottled Milk"


class VersionError(Exception):
    def __init__(self, cause):
        # message = f"Your {cause} is out of date. Please update it before continuing."
        message = "To generate rsl tourny or qualifier seeds, you must use dev-R version 5.2.117 R-1"
        with open('blind_random_settings.json', 'w') as fp:
            fp.write(message)
        super().__init__(message)


def check_rando_version():
    from version import __version__ as roman_version
    rmajor, rminor, rfix = roman_version.split()[0].split('.')
    rver = roman_version.split()[1]

    major, minor, fix = __version__.split()[0].split('.')
    ver, sver = __version__.split()[1:]

    if int(rmajor) != int(major) or int(rminor) != int(minor) or int(rfix) != int(fix):
        raise VersionError("dev-R or rando rando script")
    if int(rver[2:]) != int(ver[2:]):
        raise VersionError("dev-R")