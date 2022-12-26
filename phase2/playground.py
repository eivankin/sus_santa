import os
import warnings

from constants import MAP_FILE_PATH
from util import get_map, save_map, load_map

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    if not os.path.exists(MAP_FILE_PATH):
        sus_map = get_map()
        save_map(sus_map)
    else:
        sus_map = load_map()

    print(sus_map)
