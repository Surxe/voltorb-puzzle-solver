from src.cell import Cell, remove_options
from src.cell_set_counter import CellSetCounter
from src.utils import log

class CellSet:
    # represents 5 core cells and its Counter
    def __init__(self, _core_cells: list[Cell], _cell_set_counter: CellSetCounter):
        self.core_cells = _core_cells
        self.cell_set_counter = _cell_set_counter
    def __str__(self): #always presented horizontally, so if a column is printed it will look like a row
        string = ""
        for core_cell in self.core_cells:
            string += str(core_cell) + ' '
        string += str(self.cell_set_counter)
        return string

"""
rules:
* each individual cell can have a value of 0, 1, 2, or 3, but not 4 or more
* If 4 cell(s) must share 3 value across them and 2 cell(s) are a voltorb (0), then 2 cell(s) must share 3 value, meaning a (3, 0) or (2, 1), except there can't be a 3rd voltorb, therefore each cell has their options reduced to (2, 1) each

short: 'v value across a of b cells' 
    -> 'a cells must share v value with each having 1 or more value each 
        -> 'each of the b cells has their options reduced to <result>'

These rules can definitely be derived formulaicly but I'm not there yet
* x value across y cells with 0 voltorb(s): [1,2,3]

* v value across c cells with z voltorb(s):

* 1 value across 3 cell(s) with 1 voltorb(s): N/A
"""
all_options = [0,1,2,3]
all_options_reverse = [3,2,1,0]
def process_new_options(v, c, z):
    if v < 0:
        return None
    if v==0:
        return [0]
    if c==z:
        return None
    if c<z:
        return None
    if v==c and z==0:
        return [1]

    my_options = [1,2,3]
    
    if c>z:
        if c==1 and v in all_options: # 1 slot remains that has a possible value
            return [v]

        diff = c-z
        if diff == v:
            return [0,1]
        if diff > v:
            return None

        # 3 value across 5 cell(s) with 4 voltorb(s): 3 NOT 0,1,2
        #return [0] + new_options(v, diff, 0)
        if z != 0:
            log(f"z!=0")
            potential_new_options = process_new_options(v, diff, 0)
            if potential_new_options is not None:
                return list(set([0] + potential_new_options))
        
        for this_option in all_options_reverse:
            if c < this_option: # value is less than the option so it couldnt even fit it in one slot
                log(f"removing {this_option}")
                my_options = remove_options(my_options, [this_option]) # remove this_option
            # attempt to place this_option in one slot- does it force any slots to be a 0? if so, this_option is removed
            # 2 value across 2 cell(s) with 0 voltorbs, removed [3], down to [0,1,2], this_option==2
            v2 = v-this_option #deduct the cost of the option from the remainder, now its
            c2 = c-1 # use the slot for this_option
            # 0 value across 1 cell(s)s with 0 voltorb(s): [0]
            # 1 value across 1 cell with 0
            log(f"trying value {v2} across {c2} cells with {z} voltorbs")
            potential_new_options = process_new_options(v2, c2, z)
            # returns a 0 therefore this_option is not possible
            log(f"current options {my_options}")
            if potential_new_options is None or 0 in potential_new_options:
                log(f'this_option {this_option} wont work')
                my_options = remove_options(my_options, [this_option])
            else:
                log(f"this_option {this_option} will work")
                pass
            log(f"remaining options {my_options}")
            # otherwise the potential new option is at least possible and can continue

        return my_options
        
    raise ValueError("idiot")

def get_option_decision(v, c, z):
    return f"{v} value across {c} cell(s) with {z} voltorb(s): {process_new_options(v, c, z)}"