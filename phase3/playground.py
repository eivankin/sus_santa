import json
import os
import warnings

from constants import MAP_FILE_PATH, MAP_ID, IDS_FILE, SOLUTIONS_PATH
from checker import emulate
from data import Solution, Map, Present, Gift, Coordinates, Child
from greedy import most_expensive, get_sol_cost
from bin_packing import solve_bin_pack
from visualizer import visualize_moves
from util import (
    get_map,
    save_map,
    load_map,
    info_about_map,
    send_solution,
    get_solution_info,
    edit_json_file,
    save,
    load, path_len,
)

from dataclasses import dataclass
from dataclass_wizard import JSONWizard


@dataclass
class Presents(JSONWizard):
    presents: list[Present]


def get_presents(force=False) -> list[Present]:
    if force or not os.path.exists("p.json"):
        ps = most_expensive(sus_map.gifts, sus_map.children)
        save(Presents(ps), "p.json")
    else:
        return load(Presents, "p.json").presents


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    if not os.path.exists(MAP_FILE_PATH):
        sus_map: Map = get_map()
        save_map(sus_map)
    else:
        sus_map: Map = load_map()

    info_about_map(sus_map)

    # selected_gifts = sorted(
    #     sus_map.gifts, key=lambda g: (g.price, g.volume, g.weight))[:len(sus_map.children)]
    # presents = [Present(gift_id=g.id, child_id=i + 1) for i, g in
    #             enumerate(selected_gifts)]
    presents = get_presents()
    print('Cost:', get_sol_cost(sus_map, presents))
    packed = solve_bin_pack([sus_map.gifts[p.gift_id - 1] for p in presents])
    gift_to_children: dict[int, Child] = {p.gift_id: sus_map.children[p.child_id]
                                          for p in presents}
    bags = [p['gift_ids'] for p in packed]
    assert sorted(sum(bags, [])) == sorted([p.gift_id for p in presents])

    moves: list[Coordinates] = []
    current_pos = Coordinates(0, 0)
    actual_bags = []
    for i, b in enumerate(bags):
        bag = []
        child_coords = {(gid, gift_to_children[gid].coords()) for gid in b}
        for _ in range(len(b)):
            nearest_child = None
            min_time = 0
            min_gid = 0
            for gid, c in child_coords:
                time = path_len([current_pos, c], snow_areas=sus_map.snow_areas)
                if nearest_child is None or time < min_time:
                    nearest_child = c
                    min_time = time
                    min_gid = gid
            bag.append(min_gid)
            moves.append(nearest_child)
            child_coords.remove((min_gid, nearest_child))
        actual_bags.append(bag[::-1])

        if i != len(bags) - 1:
            moves.append(Coordinates(0, 0))

    sus_solution = Solution(map_id=MAP_ID, moves=moves, stack_of_bags=actual_bags[::-1])
    print(emulate(sus_solution, sus_map))

    image_path = "./data/route.png"
    visualize_moves(sus_map, sus_solution.moves).save(image_path)
    print(f"Saved at {image_path}...")

    if input("Send solution? y/n: ").lower() in ("y", "yes"):
        sus_response = send_solution(sus_solution)
        print(sus_response)
        if sus_response.success:
            print(get_solution_info(sus_response.round_id))
            with edit_json_file(IDS_FILE) as solution:
                solution[sus_response.round_id] = input("label: ")
            save(sus_solution, SOLUTIONS_PATH + f"{sus_response.round_id}.json")
        else:
            print("Unsuccessful")
            save(sus_solution, "./data/solution_unsuccessful.json")
