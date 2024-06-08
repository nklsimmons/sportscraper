import os

from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

from app import scrape_data

# docker exec sportscraper3-backend-1 python fetch_data.py

load_dotenv()

MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')

for league in ["MLB", "WNBA"]:
    dataset = scrape_data(league)

    n_added = 0

    client = MongoClient(MONGO_CONNECTION_STRING)

    for data in dataset:

        existing = client[league]["covers"].find_one({
            "profile": data["profile"],
            "date": data["date"],
            "game": data["game"],
        })

        if not existing:
            client[league]["covers"].insert_one(data)
            n_added += 1

    client[league]["update_record"].insert_one({
        "datetime": str(datetime.now())
    })

    print(f"{league}: {len(dataset)} records fetched, {n_added} inserted\n")
