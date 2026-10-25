import sys
sys.path.append(".")

from src.utils import list_to_str, spaced_str, log
from src.constants import *

class Cell:
    def __init__(self, options: list[int]):
        self.options = options
    def __str__(self):
        options_str = list_to_str(self.options)
        return spaced_str(options_str, LEN_MAX_OPTIONS_AS_STRING)
    def is_solved(self):
        return len(self.options) == 1 #solved if only 1 option remains
    def update(self, options_to_remove):
        self.options = remove_options(self.options, options_to_remove)
    def set(self, new_options):
        self.options = new_options

def remove_options(options, options_to_remove):
    res = [o for o in options if o not in options_to_remove]
    log(f"options: {options}, options_to_remove: {options_to_remove}, new_options: {res}")
    return res
