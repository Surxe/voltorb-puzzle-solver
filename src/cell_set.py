import sys
sys.path.append(".")

from src.cell import Cell, remove_options
from src.cell_set_counter import CellSetCounter
from src.utils import log
from src.constants import GRID_SIZE, MAX_COIN_VALUE, OPTIONS_CACHE

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
    
    def get_unsolved_core_cells(self):
        """Returns unsolved core cells"""
        return [core_cell for core_cell in self.core_cells if not core_cell.is_solved()]

    def get_solved_core_cells(self):
        return [core_cell for core_cell in self.core_cells if core_cell.is_solved()]

    def get_num_voltorbs_in_play(self):
        """Returns # of voltorbs already known & solved in this cell set"""
        return len([n for n in self.core_cells if n.options == [0]])

    def get_current_value_in_play(self):
        """Returns the amount of value the CellSet currently has amongst solved cells"""
        solved_core_cells = self.get_solved_core_cells()
        value = 0
        for solved_core_cell in solved_core_cells:
            value += solved_core_cell.options[0] #solved cell has only 1 option- the current value
        return value

    def current_options(self):
        """
        Returns all possible options any cell in the set can have
        [0,1] & [2,3] -> [0,1,2,3]
        """
        distinct = set()
        for core_cell in self.core_cells:
            for option in core_cell.options:
                distinct.add(option)
        return list(distinct)
    
    def update(self):
        """
        For a CellSet with n unsolved cells, v value, and z voltorbs
            each unsolved cell has options from process_options_to_remove(v, n, z, set_options) removed
        """
        before = str(self)
        unsolved_cells = self.get_unsolved_core_cells()
        v = self.cell_set_counter.value - self.get_current_value_in_play()
        c = len(unsolved_cells)
        z = self.cell_set_counter.voltorbs - self.get_num_voltorbs_in_play()
        options_to_remove = process_options_to_remove(
            v=v, 
            c=c,
            z=z,
            set_options=self.current_options()
        )
        for core_cell in unsolved_cells:
            core_cell.update(options_to_remove)
        after = str(self)
        log(f"CellSet.update() - (v={v},c={c},z={z}) - Before: {before}, Removed: {options_to_remove}, After: {after}", do_log=True)
        

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
def _process_new_options(v, c, z, set_options):
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
    if set_options is None:
        return None

    my_options = remove_options(set_options, [0]) # never try 0 below, all voltorbs already subtracted from options
    
    if c>z:
        if c==1 and v in set_options: # 1 slot remains that has a possible value
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
            potential_new_options = process_new_options(v, diff, 0, set_options)
            if potential_new_options is not None:
                return list(set([0] + potential_new_options))
        
        for this_option in set_options:
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
            potential_new_options = process_new_options(v2, c2, z, set_options)
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

def process_new_options(v, c, z, set_options):
    """Wrapper for _process_new_options that also caches the input/output and re-uses it"""
    key = f"{v}-{c}-{z}-{set_options}" #flatten
    if key in OPTIONS_CACHE:
        return OPTIONS_CACHE[key]
    result = _process_new_options(v, c, z, set_options)
    OPTIONS_CACHE[key] = result
    return result

def process_options_to_remove(v, c, z, set_options):
    new_options = process_new_options(v, c, z, set_options)
    log(f"new_options: {new_options}", do_log=True)
    if new_options is None:
        removed_options = set_options
    else:
        removed_options = [option for option in set_options if option not in new_options]
    return removed_options

def cache_to_disk():
    with open(encoding='utf-8', mode='w', file='cache/options.txt') as f:
        for key, options in OPTIONS_CACHE.items():
            f.write(f"{key}: {options}\n")
    
def get_option_decision(v, c, z):
    return f"{v} value across {c} cell(s) with {z} voltorb(s): {process_new_options(v, c, z, [0,1,2,3])}"

if __name__ == '__main__': #for funzies
    # try all
    for v in range(0, MAX_COIN_VALUE+1):
        for c in range(1, GRID_SIZE+1):
            for z in range(0, c+1):
                log(get_option_decision(v, c, z), do_log=True)
    set_options=[0,1,2,3]
    remaining_options = process_new_options(3, 5, 2, set_options)
    removed_options = process_options_to_remove(3, 5, 2, set_options)
    print(f"remaining_options: {remaining_options}, removed_options: {removed_options}")