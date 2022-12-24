from util import get_solution_info
from data import RoundInfo
from constants import IDS_FILE
import json

CACHE_FILE = ".status_cache.json"

if __name__ == "__main__":
    status_cache = {}
    try:
        with open(CACHE_FILE, "r") as status_cache_file:
            status_cache = json.load(status_cache_file)
    except:
        pass
    with open(IDS_FILE, "r") as solution_file:
        content = json.load(solution_file)
        for round_id, msg in content.items():
            print(round_id + ":")
            print(f'"{msg}"')
            if round_id not in status_cache:
                solinf = get_solution_info(round_id)
                if solinf.data.status == "processed":
                    status_cache[round_id] = solinf.to_dict()
            else:
                solinf = RoundInfo.from_dict(status_cache[round_id])
            print(solinf)
    with open(CACHE_FILE, "w") as status_cache_file:
        json.dump(status_cache, status_cache_file)
