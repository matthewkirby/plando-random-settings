import ast
import os
import json

from multiselects import ms_option_lookup
from randomizer.SettingsList import SettingInfos
import roll_settings as rs


def validate_rsl(weights, verbose=False):
    validate_weights(weights)
    validate_multiselect_knowledge()
    validate_conditionals(verbose)
    validate_overrides()


def validate_weights(weights, check_existing=True, check_missing=True, print_headings=True):
    """ Function to check for new settings and options when the randomizer is updated. """
    # Settings to not care about validating if they show up in balanced weights because they are handled manually
    ignore_settings = ["custom_ice_trap_percent", "custom_ice_trap_count", "hint_dist"] + list(ms_option_lookup.keys())
    # Settings not to care about missing options (enumerations)
    ignore_options = ["special_deal_price_min", "special_deal_price_max"]

    randomizer_settings = rs.generate_balanced_weights(None)

    # Find new or changed settings by name
    changed_settings = []
    if print_headings:
        print("Checking for new or removed settings...")
    rsl_settings_set = set(weights.keys())
    ootr_settings_set = set(randomizer_settings.keys())
    if check_existing: # Check settings in weights file still exist
        for setting in rsl_settings_set-ootr_settings_set:
            changed_settings.append(f"\tRSL:  {setting} {list(weights[setting].keys())}")
    if check_missing: # Check OoTR Settings to find anything missing in weights
        for setting in ootr_settings_set-rsl_settings_set:
            if setting not in ignore_settings:
                changed_settings.append(f"\tOoTR: {setting} {list(SettingInfos.setting_infos[setting].choice_list)}")
    for line in changed_settings:
        print(line)

    # Find new or changed options
    if print_headings:
        print("\nChecking settings for new or removed options...")
    for setting, optweights in weights.items():
        if setting in ignore_settings:
            continue
        rsl_options = set(optweights.keys())
        ootr_options = set(map(lambda x: str(x).lower(), SettingInfos.setting_infos[setting].choice_list))
        if check_existing: # Only check that the options in the weights still exist
            for option in rsl_options-ootr_options:
                print(f"\tRSL:  {setting}:{option} removed or renamed")
        if check_missing: # Only check that the weight has all options for each setting
            for option in ootr_options-rsl_options:
                if setting not in ignore_options:
                    print(f"\tOoTR: {setting}:{option} newly added")


def validate_multiselect_knowledge():
    print("\nVerifying multiselect knowledge...")
    for mskey in ms_option_lookup.keys():
        rslset = set(ms_option_lookup[mskey])
        ootrset = set(SettingInfos.setting_infos[mskey].choice_list)
        if rslset != ootrset:
            print(f"\t{mskey} mismatched!")
            print(f"\t\tRSL:  {rslset-ootrset}")
            print(f"\t\tOoTR: {ootrset-rslset}")



def validate_overrides():
    print("\nValidating override files...")
    override_dir = "weights"
    for fname in os.listdir(override_dir):
        if fname.endswith(".json") and fname != "rsl_main.json":
            print(f"  > {fname}")
            with open(os.path.join(override_dir, fname)) as f:
                data = json.load(f)
            if "weights" in data:
                validate_weights(data["weights"], check_missing=False, print_headings=False)




class RSLVisitor(ast.NodeVisitor):
    def __init__(self):
        self.setting_references = [] # [setting, ...]
        self.option_references = [] # [(setting, option), ...]

    def _subscript_checker_(self, node):
        # Type checking to identify a node as `random_settings["key"]`
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == 'random_settings'
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            return True
        return False

    def visit_Subscript(self, node):
        # Nodes matching key/value pair references
        # Find all `random_settings["key"]` nodes
        if self._subscript_checker_(node):
            self.setting_references.append(node.slice.value)
        self.generic_visit(node) # Recursively check children

    def visit_Assign(self, node):
        # Nodes matching assignment operations
        # Only checking when assignments are string literals
        # Checking options set as values in random_settings dict
        for target in node.targets:
            if (
                isinstance(target, ast.Subscript)
                and self._subscript_checker_(target)
                and isinstance(node.value, ast.Constant)
            ):
                self.option_references.append((target.slice.value, node.value.value))
        self.generic_visit(node)


def summarize_conditionals():
    """ For each conditional function, return the associated visitor instance """
    results = {}
    ignore_functions = ["parse_conditionals"]
    with open("conditionals.py") as fin:
        tree = ast.parse(fin.read())

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name not in ignore_functions:
            visitor = RSLVisitor()
            visitor.visit(node)
            results[node.name] = visitor
    return results


def validate_conditionals(verbose):
    print("\nValidating dictionary keys in conditionals...")
    results = summarize_conditionals()
    for funcname, visitor in results.items():
        print(f"  > {funcname} ".ljust(64, '='))
        for setting in visitor.setting_references:
            if setting not in SettingInfos.setting_infos:
                print(f"    X {setting} referenced but not found.")
            elif verbose: print(f"    - {setting} referenced and okay.")
        for (setting, option) in visitor.option_references:
            # Handle the boolean option (doing it this way here is easier than transforming everything like I do elsewhere)
            if option == "true": option = True
            elif option == "false": option = False

            if option not in SettingInfos.setting_infos[setting].choice_list:
                print(f"    X {setting} has no option {option}.")
                print(f"       - Valid options are: {SettingInfos.setting_infos[setting].choice_list}")
            elif verbose: print(f"    - {setting}:{option} is okay.")



# What types of expressions exist in the conditionals that I still want to validate?
# In `exclude_minimal_triforce_hunt`:
#           weights = weight_dict['item_pool_value']
#           if 'minimal' in weights.keys()
#   - weight_dict is already validated up above
#   - If I can establish that this is the standard practice of extracting weights for 1 setting
#     from the full weight dict, I can validate that when I look for an option that option still
#     exists in the weights
#   - Alternatively, I can look for assignment that has a Subscript of weight_dict on the RHS. That
#     would allow me to relax the requirement its called `weights` because this tells me the variable
#     name. Then I can find any `in` operations
#
#           random_settings['triforce_hunt'] == "true"
#   - Check equality operations when one of the sides is random_settings
#
# In `exclude_ice_trap_misery`:
#           random_settings['damage_multiplier'] in ['quadruple', 'ohko']
#   - This is the same sort of thing as `random_settings['x'] == y`. Just need to ensure it also finds these
#
# In `restrict_one_entrance_randomizer`:
#           erlist = ["shuffle_interior_entrances:off", "shuffle_grotto_entrances:false", "shuffle_dungeon_entrances:off",
#                     "shuffle_overworld_entrances:false"]
#   - I need to validate setting:options pairs defined in this way
#   - It may be easier to refactor how I define these pairs in the conditional code
#
# In `random_scrubs_start_wallet`
#           extra_starting_items['starting_equipment'] += ['wallet']
#   - This can be checked the same way I check options
#   - `extra_starting_items` is a list that every conditional is passed