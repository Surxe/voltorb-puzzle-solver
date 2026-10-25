from backend.utils import list_to_str, spaced_str
from backend.constants import LEN_MAX_OPTIONS_AS_STRING, VOLTORB

class Cell:
    # a single card on the board: the options it may still hold, and whether it has been flipped in the game
    def __init__(self, options: list[int]):
        self.options = sorted(options)
        self.revealed = False
    def __str__(self):
        options_str = list_to_str(self.options)
        return spaced_str(options_str, LEN_MAX_OPTIONS_AS_STRING)
    def is_safe(self):
        """True when the cell can't be a voltorb"""
        return VOLTORB not in self.options
    def could_multiply(self):
        """True when the cell may still be worth flipping: a 2 or 3 multiplies the coins, a 1 changes nothing"""
        return any(option > 1 for option in self.options)
    def set(self, new_options) -> bool:
        """Replaces the options; returns whether they changed"""
        new_options = sorted(new_options)
        changed = new_options != self.options
        self.options = new_options
        return changed
    def reveal(self, value: int):
        """The card was flipped in the game and showed value"""
        self.set([value])
        self.revealed = True
