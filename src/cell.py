from utils import list_to_str, spaced_str
from constants import *

class Cell:
    def __init__(self, options: list[int]):
        self.options = options
    def __str__(self):
        options_str = list_to_str(self.options)
        return spaced_str(options_str, LEN_MAX_OPTIONS_AS_STRING)