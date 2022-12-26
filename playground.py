import json
from util import (
    get_map,
    edit_json_file,
    read_json_file,
    send_solution,
    get_solution_info,
    save_map,
    load_map,
    save,
    load_bags,
)
from data import Path, Route, Coordinates, Line, Circle
from constants import MAP_ID, MAP_FILE_PATH, IDS_FILE, PRECALC_BASE_FILE
import os
from checker import emulate
import visualizer
from tqdm import tqdm
from precalc_base_path import (
    ObjectiveChecker,
    OprimalPathFromBaseFinder,
    PathFromBaseMutator,
    PenatyChecker,
)

import warnings

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()

    circles = [Circle.from_snow(s) for s in sus_map.snow_areas]
    penalty = PenatyChecker(circles).penalty
    objective = ObjectiveChecker(penalty).objective

    cache_misses = []
    cache_hits = []
    cache = {}
    # with read_json_file(PRECALC_BASE_FILE) as precalc:
    #     for k, v in precalc.items():
    #         cache[Coordinates.from_str(k)] = Path.from_dict(v)

    def optimal_path(start: Coordinates, f: Coordinates) -> list[Coordinates]:
        if f in cache:
            cache_hits.append(f.to_str())
            return cache[f].path[1:-1]
        else:
            cache_misses.append(f.to_str())

        segmentation = max(int(f.dist(start) / 2_000), 5)
        if segmentation == 0:
            return []

        return (
            OprimalPathFromBaseFinder(
                segmentation,
                PathFromBaseMutator(1000, 1000).mutate,
                objective,
                schedule={"tmax": 100, "tmin": 1, "steps": 1_000, "updates": 0},
            )
            .optimal_path(start, f)
            .path[1:-1]
        )

    stack_of_bags = load_bags()
    stack_of_bags.sort(key=len, reverse=True)

    moves = []
    base = Coordinates(0, 0)
    curr_pos = Coordinates(0, 0)

    unvisited = set(child_pos for child_pos in sus_map.children)
    for bag in tqdm(
        list(reversed(stack_of_bags))
    ):  # since it's a stack, the order is reversed
        for i, _ in enumerate(bag):
            # while we have gifts in a bag
            # the strategy is to give these gifts to the nearest children
            nearest_child_pos = None
            metric = 10**100
            for child_pos in unvisited:
                m = child_pos.dist(curr_pos)
                if m >= metric:
                    continue
                # m = out_circ + 7*in_circ = (m - in_circ) + 7 * in_circ
                m += 6 * penalty(child_pos, curr_pos)
                if nearest_child_pos is None or m < metric:
                    nearest_child_pos = child_pos
                    metric = m
            # if i == 0:
            #     assert curr_pos == base
            #     # go to the first child using segmented path
            moves.extend(optimal_path(curr_pos, nearest_child_pos))
            moves.append(nearest_child_pos)
            curr_pos = nearest_child_pos
            unvisited.remove(nearest_child_pos)

        # go back using segmented path
        if len(unvisited) != 0:
            moves.extend(reversed(optimal_path(base, curr_pos)))
            moves.append(base)
            curr_pos = base

    sus_solution = Route(moves=moves, map_id=MAP_ID, stack_of_bags=stack_of_bags)
    print("=== SOLUTION ===")
    print(sus_solution)
    print("cache misses: " + json.dumps(cache_misses))
    print("cache hits: " + json.dumps(cache_hits))
    visualizer.visualize_route(sus_map, sus_solution).save("data/route.png")
    print(emulate(sus_solution, sus_map))
    if input("Send solution? y/n: ").lower() in ("y", "yes"):
        sus_response = send_solution(sus_solution)
        print("=== RESPONSE ===")
        print(sus_response)
        print("=== INFO ===")
        if sus_response.success:
            print(get_solution_info(sus_response.round_id))
            with edit_json_file(IDS_FILE) as solution:
                solution[sus_response.round_id] = input("label: ")
            save(sus_solution, f"./data/solution_{sus_response.round_id}.json")
        else:
            print("Unsuccessful")
            save(sus_solution, "./data/solution_unsuccessful.json")
