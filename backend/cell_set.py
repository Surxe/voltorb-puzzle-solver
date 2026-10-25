from functools import cache
from itertools import product

from backend.cell import Cell
from backend.cell_set_counter import CellSetCounter
from backend.constants import VOLTORB
from backend.errors import Contradiction
from backend.utils import log

class CellSet:
    # represents the core cells of a row or column and its Counter
    def __init__(self, _core_cells: list[Cell], _cell_set_counter: CellSetCounter):
        self.core_cells = _core_cells
        self.cell_set_counter = _cell_set_counter
    def __str__(self): #always presented horizontally, so if a column is printed it will look like a row
        string = ""
        for core_cell in self.core_cells:
            string += str(core_cell) + ' '
        string += str(self.cell_set_counter)
        return string

    def current_options(self):
        """
        Returns all possible options any cell in the set can have
        [0,1] & [2,3] -> [0,1,2,3]
        """
        return sorted({option for core_cell in self.core_cells for option in core_cell.options})

    def arrangements(self) -> list[tuple[int, ...]]:
        """Every assignment of one option per core cell that matches the counter"""
        counter = self.cell_set_counter
        return [
            arrangement for arrangement in product(*(core_cell.options for core_cell in self.core_cells))
            if sum(arrangement) == counter.value and arrangement.count(VOLTORB) == counter.voltorbs
        ]

    def update(self, do_log=False) -> bool:
        """
        Reduces each core cell's options to those that appear in at least one arrangement matching the counter.
        Solved cells take part like any other cell, so value/voltorbs already in play are accounted for.
        Returns whether any cell changed; raises Contradiction when no arrangement exists.
        """
        before = str(self)
        supported = supported_options(
            [core_cell.options for core_cell in self.core_cells],
            self.cell_set_counter.value,
            self.cell_set_counter.voltorbs,
        )
        if supported is None:
            raise Contradiction(f"no arrangement of [{before}] matches its counter")
        changed = False
        for core_cell, options in zip(self.core_cells, supported):
            changed |= core_cell.set(options)
        if changed:
            log(f"CellSet.update() - Before: {before}, After: {self}", do_log=do_log)
        return changed


def supported_options(domains: list[list[int]], value: int, voltorbs: int) -> list[list[int]] | None:
    """
    Given cells whose options are `domains`, that together must hold exactly `value` value and `voltorbs` voltorbs,
    returns each cell's options reduced to the ones that appear in at least one valid arrangement,
    or None if there is no valid arrangement.

    An option o in cell i is supported when the cells before i can reach some (value, voltorbs) total
    and the cells after i can reach exactly what remains once o is placed:
        [0,1,2] [0,1,2], 4 value, 0 voltorbs -> 3 and 1 can't fit -> [2] [2]
    """
    def step(totals, options):
        return {
            (v + o, z + (o == VOLTORB))
            for v, z in totals for o in options
            if v + o <= value and z + (o == VOLTORB) <= voltorbs
        }

    # prefix[i]: (value, voltorbs) totals reachable by cells [0, i); suffix[i]: by cells [i, n)
    prefix = [{(0, 0)}]
    for options in domains:
        prefix.append(step(prefix[-1], options))
    suffix = [{(0, 0)}]
    for options in reversed(domains):
        suffix.append(step(suffix[-1], options))
    suffix.reverse()

    if (value, voltorbs) not in prefix[-1]:
        return None
    return [
        [
            o for o in options
            if any((value - v - o, voltorbs - z - (o == VOLTORB)) in suffix[i + 1] for v, z in prefix[i])
        ]
        for i, options in enumerate(domains)
    ]

@cache
def _process_new_options(v, c, z, set_options: tuple[int, ...]):
    supported = supported_options([list(set_options)] * c, v, z)
    if supported is None:
        return None
    return sorted({option for options in supported for option in options})

def process_new_options(v, c, z, set_options):
    """
    v value across c cells with z voltorbs, where each cell may be any of set_options
        -> every option some cell could still hold, or None if it can't be done
    3 value across 3 cell(s) with 1 voltorb(s), [0,1,2,3] -> [0,1,2]
    4 value across 2 cell(s) with 0 voltorb(s), [0,1,2] -> [2] (a 3 and a 1 isn't possible, so 2 and 2)
    """
    return _process_new_options(v, c, z, tuple(set_options))

def process_options_to_remove(v, c, z, set_options):
    new_options = process_new_options(v, c, z, set_options)
    if new_options is None:
        return list(set_options)
    return [option for option in set_options if option not in new_options]

def get_option_decision(v, c, z, set_options):
    return f"{v} value across {c} cell(s) with {z} voltorb(s): {process_new_options(v, c, z, set_options)}"
