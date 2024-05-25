#!/usr/bin/env python
from dotenv import load_dotenv
import os

from pprint import pprint
from flask import Flask
from pymongo import MongoClient
from test import get


load_dotenv()

MONGODB_CONTAINER = os.getenv('MONGODB_CONTAINER')

app = Flask(__name__)
client = MongoClient(f"mongodb://{MONGODB_CONTAINER}")


@app.route("/")
def index():

    data = []

    for item in client["MLB"]["covers"].find():
        data.append(item)

    return str(data)


@app.route("/run")
def run():
    dataset = get()

    for data in dataset:
        existing = client["MLB"]["covers"].find_one({
            "profile": data["profile"],
            "date": data["date"],
            "game": data["game"],
        })

        if not existing:
            client["MLB"]["covers"].insert_one(data)

    return "Success"


# @app.route('/')
# def todo():
#     try:
#         client.admin.command('ismaster')
#     except:
#         return "Server not available"
#     return "Hello from the MongoDB client!\n"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
