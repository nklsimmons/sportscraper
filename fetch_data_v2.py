import os

from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

from functions import dump
from app import scrape_data, get_money_leaders_picks
from pprint import pprint

# docker exec sportscraper-backend python fetch_data_v2.py

load_dotenv()

MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')

LEAGUES = ["MLB", "WNBA", "NCAAF", "NBA", "NFL"]

for league in LEAGUES:
    if league == "MLB":
        totalPicks = 500
        sidesOrderPickBy = "StraightUp"
        totalsOrderPickBy = "Totals"
    else:
        totalPicks = 100
        sidesOrderPickBy = "Ats"
        totalsOrderPickBy = "Totals"

    sides_data = get_money_leaders_picks(league, totalPicks=totalPicks, orderPickBy=sidesOrderPickBy)
    totals_data = get_money_leaders_picks(league, totalPicks=totalPicks, orderPickBy=totalsOrderPickBy)

    n_added = 0

    client = MongoClient(MONGO_CONNECTION_STRING)

    for profile in sides_data:

        for pick in profile.get("picks", []):

            existing = client[league]["covers_v2"].find_one({
                "user": profile["user"],
                "date": pick["date"],
                "game": pick["game"],
                "type": "sides",
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
                "type": "sides",
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

    for profile in totals_data:

        for pick in profile.get("picks", []):

            existing = client[league]["covers_v2"].find_one({
                "user": profile["user"],
                "date": pick["date"],
                "game": pick["game"],
                "type": "totals"
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
                "type": "totals",
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
