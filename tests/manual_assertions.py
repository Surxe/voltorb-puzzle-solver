import sys
sys.path.append(".")

from src.utils import *
from src.cell_set import process_new_options, get_option_decision, cache_to_disk

path = 'tests/manual_assertions.txt'
lines_list = []
with open(encoding='utf-8', mode='r', file=path) as lines:
    for line in lines:
        lines_list.append(line.strip())
    
count = 0
for v in range(1, 4):
    for c in range(1, 6):
        for z in range(0, c+1):
            calculation = get_option_decision(v, c, z, [0,1,2,3]) #for this test we essentially ignore limiting factors across the set
            expectation = lines_list[count].replace(',', ', ')
            
            if not calculation==expectation:
                print(f"calculation: {calculation}, \nexpectation: {expectation}\n")

            count += 1

cache_to_disk()