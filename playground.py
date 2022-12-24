from util import get_map, send_solution, get_solution_info, save_map, load_map
from data import Route, Coordinates, Line, Circle
from constants import MAP_ID, MAP_FILE_PATH, IDS_FILE
import os
from checker import emulate
import visualizer
import json
from tqdm import tqdm

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

    moves = []
    curr_pos = Coordinates(0, 0)
    unvisited = set(child_pos for child_pos in sus_map.children)
    with tqdm(total=sum(len(bag) for bag in stack_of_bags)) as pbar:
        for bag in reversed(stack_of_bags):  # since it's a stack, the order is reversed
            for _ in bag:
                nearest_child_pos = None
                metric = 10**100
                for child_pos in unvisited:
                    m = child_pos.dist(curr_pos)
                    if m > metric:
                        continue
                    l = Line.from_two_points(curr_pos, child_pos)
                    d_circ = sum(
                        l.distance_in_circle(Circle.from_snow(s))
                        for s in sus_map.snow_areas
                    )
                    # m = out_circ + 7*in_circ = (m - d_circ) + 7 * d_circ
                    m += 6 * d_circ
                    if nearest_child_pos is None or m < metric:
                        nearest_child_pos = child_pos
                        metric = m
                moves.append(nearest_child_pos)
                curr_pos = nearest_child_pos
                unvisited.remove(nearest_child_pos)
                pbar.update(1)
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
            content[sus_response.round_id] = "second dummy strategy with circle slowing"
            json.dump(content, solution_file)
    else:
        print("Unsuccessful")
