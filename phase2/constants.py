from dotenv import load_dotenv

import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
MAP_ID = os.getenv("MAP_ID")

BASE_URL = "https://datsanta.dats.team"
SUBMISSION_URL = BASE_URL + "/api/round2"
INFO_URL_TEMPLATE = SUBMISSION_URL + "/%s"
MAP_URL = BASE_URL + f"/json/map/{MAP_ID}.json"
AUTH_HEADER = {"X-API-Key": API_KEY}

IDS_FILE = "./data/.round_ids.json"
CACHE_FILE = "./data/.status_cache.json"
MAP_FILE_PATH = "./data/map.json"
SOLUTIONS_PATH = "./data/solutions/"

# Game constants
MAX_MONEY = 100000
MIN_AGE = 0
MAX_AGE = 10
