import json, random, sys, os, traceback, argparse
import rsl_tools as tools
import roll_settings as rs
tools.check_version()


# Please set the weights file you with to load
weights = "RSL" # The default Random Settings League Season 2 weights
# weights = "full-random" # Every setting with even weights
# weights = "my_weights.json" # Provide your own weights file. If the specified file does not exist, this will create one with equal weights
# global_override_fname = "multiworld_override.json"
# global_override_fname = "ddr_override.json"
# global_override_fname = "beginner_override.json"
# global_override_fname = "coop_override.json"


# Handle all uncaught exceptions with logging
def error_handler(type, value, tb):
    with open("ERRORLOG.TXT", 'w') as errout:
        traceback.print_exception(type, value, tb, file=errout)
        traceback.print_exception(type, value, tb, file=sys.stdout)
sys.excepthook = error_handler


def cleanup_previous_run():
    # Delete residual files from previous runs
    remove_me = [os.path.join("data", "random_settings.json"), "ERRORLOG.TXT"]
    for file_to_delete in remove_me:
        if os.path.isfile(file_to_delete):
            os.remove(file_to_delete)


def get_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no_seed", help="Suppresses the generation of a patch file.", action="store_true")
    parser.add_argument("--override", help="Use the specified weights file over the default RSL weights.")
    parser.add_argument("--worldcount", help="Generate a seed with more than 1 world.")
    parser.add_argument("--check_new_settings", help="When the version updates, run with this flag to find changes to settings names or new settings.", action="store_true")
    
    args = parser.parse_args()

    # Parse weights override file
    if args.override is not None:
        if "global_override_fname" in globals():
            raise RuntimeError("RSL GENERATOR ERROR: OVERRIDE PROVIDED AS GLOBAL AND VIA COMMAND LINE.")
        if not os.path.isfile(os.path.join("weights", args.override)):
            raise FileNotFoundError("RSL GENERATOR ERROR: CANNOT FIND SPECIFIED OVERRIDE FILE IN DIRECTORY: weights")
        override = args.override
    elif "global_override_fname" in globals():
        override = global_override_fname
    else:
        override = None

    # Parse multiworld world count
    worldcount = 1
    if args.worldcount is not None:
        worldcount = int(args.worldcount)

    return args.no_seed, worldcount, override, args.check_new_settings


def main():
    no_seed, worldcount, override_weights_fname, check_new_settings = get_command_line_args()

    # If we only want to check for new/changed settings
    if check_new_settings:
        _, rslweights = rs.load_weights_file("random_settings_league_s2.json")
        tools.check_for_setting_changes(rslweights, rs.generate_balanced_weights(None))
        return

    # Clean up residual files from previous run
    cleanup_previous_run()

    max_retries = 3
    for i in range(max_retries):
        rs.generate_plando(weights, override_weights_fname)
        tools.init_randomizer_settings(worldcount=worldcount)
        completed_process = tools.generate_patch_file() if not no_seed else None
        if completed_process is None or completed_process.returncode == 0:
            break
        if i == max_retries-1 and completed_process.returncode != 0:
            raise RuntimeError(completed_process.stderr.decode("utf-8"))

    if not no_seed:
        print(completed_process.stderr.decode("utf-8").split("Patching ROM.")[-1])


if __name__ == "__main__":
    main()
