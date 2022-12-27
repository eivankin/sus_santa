import os
import warnings

from constants import MAP_FILE_PATH, MAP_ID, IDS_FILE, SOLUTIONS_PATH
from phase3.data import Solution, Map
from util import (
    get_map,
    save_map,
    load_map,
    info_about_map,
    send_solution,
    get_solution_info,
    edit_json_file,
    save,
    load,
)

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    if not os.path.exists(MAP_FILE_PATH):
        sus_map: Map = get_map()
        save_map(sus_map)
    else:
        sus_map: Map = load_map()

    info_about_map(sus_map)

    sus_solution = Solution(MAP_ID, )

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
