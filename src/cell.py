from utils import list_to_str, spaced_str, log
from constants import *

class Cell:
    def __init__(self, options: list[int]):
        self.options = options
    def __str__(self):
        options_str = list_to_str(self.options)
        return spaced_str(options_str, LEN_MAX_OPTIONS_AS_STRING)

def remove_options(options, options_removed):
    res = [o for o in options if o not in options_removed]
    log(f"options: {options}, options_removed: {options_removed}, new_options: {res}")
    return res
