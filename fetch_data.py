import os

from dotenv import load_dotenv
from pymongo import MongoClient

from app import scrape_data

from pprint import pprint


load_dotenv()

MONGODB_CONTAINER = os.getenv('MONGODB_CONTAINER')

dataset = scrape_data()

n_added = 0

client = MongoClient(f"mongodb://{MONGODB_CONTAINER}")

for data in dataset:

    existing = client["MLB"]["covers"].find_one({
        "profile": data["profile"],
        "date": data["date"],
        "game": data["game"],
    })

    if not existing:
        client["MLB"]["covers"].insert_one(data)
        n_added += 1

print(f"{len(dataset)} records fetched, {n_added} inserted")
