from src.utils import spaced_str
from src.constants import *

class CellSetCounter:
    # represents the sum value & voltorbs of either a row or a column
    #. e.g.. top row may contain exactly 2 voltorbs and exactly 3 value
    def __init__(self, _value: int, _voltorbs: int):
        self.value = _value
        self.voltorbs = _voltorbs
    def __str__(self):
        return spaced_str(f"{self.value},{self.voltorbs}", LEN_MAX_OPTIONS_AS_STRING)