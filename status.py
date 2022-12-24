from util import get_solution_info
import json

if __name__ == "__main__":
    with open(".round_ids.json", "r") as solution_file:
        content = json.load(solution_file)
        for round_id, msg in content.items():
            print(round_id + ":")
            print(msg)
            print(get_solution_info(round_id))
