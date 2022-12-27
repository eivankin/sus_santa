from dotenv import load_dotenv

import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
MAP_ID = os.getenv("MAP_ID")

BASE_URL = "https://datsanta.dats.team"
SUBMISSION_URL = BASE_URL + "/api/round"
INFO_URL_TEMPLATE = SUBMISSION_URL + "/%s"
MAP_URL = BASE_URL + f"/json/map/{MAP_ID}.json"
AUTH_HEADER = {"X-API-Key": API_KEY}

MAP_FILE_PATH = "./data/map.json"
TIMES_MATRIX_PATH = "./data/matrix_old.json"

IDS_FILE = ".round_ids.json"

PRECALC_BASE_FILE = "./data/precalc_base.json"

# Game constants
BAG_MAX_WEIGHT = 200
BAG_MAX_VOLUME = 100
BASE_SPEED = 70
SNOW_SPEED = 10
WIND_SPEED = 10
MAX_COORD = 10_000
