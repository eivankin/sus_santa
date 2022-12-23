from util import get_map, send_solution, get_solution_info, save_map, load_map
from data import Route, Coordinates
from constants import MAP_ID, MAP_FILE_PATH
import os
from checker import emulate

if __name__ == '__main__':
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()

    stack_of_bags = []
    for gift in sus_map.gifts:
        stack_of_bags.append([gift.id])

    moves = []
    for child in sus_map.children:
        moves.append(Coordinates(child.x, child.y))
        moves.append(Coordinates(0, 0))

    sus_solution = Route(moves=moves, map_id=MAP_ID,
                         stack_of_bags=stack_of_bags)
    print('=== SOLUTION ===')
    print(sus_solution)
    print(emulate(sus_solution, sus_map))
