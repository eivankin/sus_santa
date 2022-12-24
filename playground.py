from util import get_map, send_solution, get_solution_info, save_map, load_map
from data import Route, Coordinates
from constants import MAP_ID, MAP_FILE_PATH, IDS_FILE
import os
from checker import emulate
import visualizer
import json

if __name__ == "__main__":
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()

    stack_of_bags = []
    with open("data/bin_packing_result.json", "r") as f:
        for bag in json.load(f):
            stack_of_bags.append(bag["gift_ids"])

    stack_of_bags.reverse()

    # strategy is to target the nearest child until bag is empty (second dummy strategy)
    moves = []
    curr_pos = Coordinates(0, 0)
    unvisited = set(child_pos for child_pos in sus_map.children)
    for bag in stack_of_bags:
        for _ in bag:
            nearest_child_pos = None
            metric = 10**100
            for child_pos in unvisited:
                d = child_pos.dist(curr_pos)
                if nearest_child_pos is None or d < metric:
                    nearest_child_pos = child_pos
                    metric = d
            moves.append(nearest_child_pos)
            curr_pos = nearest_child_pos
            unvisited.remove(nearest_child_pos)
        moves.append(Coordinates(0, 0))
        curr_pos = Coordinates(0, 0)

    sus_solution = Route(moves=moves, map_id=MAP_ID, stack_of_bags=stack_of_bags)
    print("=== SOLUTION ===")
    print(sus_solution)
    visualizer.visualize_route(sus_map, sus_solution).save("data/route.png")
    # print(emulate(sus_solution, sus_map))
    sus_response = send_solution(sus_solution)
    print("=== RESPONSE ===")
    print(sus_response)
    print("=== INFO ===")
    if sus_response.success:
        print(get_solution_info(sus_response.round_id))
        content = None
        try:
            with open(IDS_FILE, "r") as solution_file:
                content = json.load(solution_file)
        except:
            content = {}
        with open(IDS_FILE, "w") as solution_file:
            content[sus_response.round_id] = "reversed, but not reversed"
            json.dump(content, solution_file)
    else:
        print("Unsuccessful")
