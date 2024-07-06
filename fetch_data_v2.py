import os

from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

from functions import dump
from app import scrape_data, scrape_data_v2
from pprint import pprint

# docker exec sportscraper3-backend-1 python fetch_data.py

load_dotenv()

MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')

for league in ["MLB"]:
    dataset = scrape_data_v2(league)

    n_added = 0

    client = MongoClient(MONGO_CONNECTION_STRING)

    for profile in dataset:

        for pick in profile.get("picks", []):

            existing = client[league]["covers_v2"].find_one({
                "profile": profile["user"],
                "date": pick["date"],
                "game": pick["game"],
            })

            if existing:
                continue

            pick_f = {}

            if pick["pick"]["ou"] is not None:
                pick_f["O/U"] = pick["pick"]["ou"].split(' ')
            else:
                pick_f["O/U"] = None

            if pick["pick"]["sides"] is not None:
                pick_f["Side"] = pick["pick"]["sides"].split(' ')
            else:
                pick_f["Side"] = None

            data = {
                "date": pick["date"],
                "game": pick["game"],
                "status": pick["status"],
                "rank": profile["rank"],
                "sides": profile["sides"],
                "units": profile["units"],
                "user": profile["user"],
                "win_rate": profile["win_rate"],
                "diff": profile["diff"],
                "pending_picks_url": profile["pending_picks_url"],
                "pick": pick_f
            }
            client[league]["covers_v2"].insert_one(data)
            n_added += 1

    client[league]["update_record"].insert_one({
        "datetime": str(datetime.now())
    })

    print(f"{league}: {n_added} records inserted\n")
