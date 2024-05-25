#!/usr/bin/env python
from dotenv import load_dotenv
import os
import json

from flask import Flask, render_template
from pymongo import MongoClient

from app import scrape_data


load_dotenv()

MONGODB_CONTAINER = os.getenv('MONGODB_CONTAINER')

app = Flask(__name__)
client = MongoClient(f"mongodb://{MONGODB_CONTAINER}")


def dump(v):
    return json.loads(json.dumps(v))

@app.route("/")
def index():
    data_by_date = {}
    games = set()

    # Get all relevant dates
    todays_date = "Saturday, May 25"
    todays = client["MLB"]["covers"].find({"date": todays_date})
    for t in todays:
        games.add(t["game"])

    game_data = dict()
    for game in games:
        try:
            game_data[game]
        except KeyError:
            game_data[game] = {"games": [], "summary": dict()}

        todays_games = client["MLB"]["covers"].find(
            {
                "game": game,
                "date": todays_date
            }, {"_id": 0})

        over_under_count = []
        sides_count = dict()

        for tg in todays_games:

            if tg["pick"].get("O/U"):

                over_under_value = float(tg["pick"].get("O/U")[1])
                if tg["pick"].get("O/U")[0] == "Under":
                    over_under_value = over_under_value * -1

                over_under_count.append(over_under_value)

            if tg["pick"].get("Side"):
                side = tg["pick"].get("Side")[0]

                try:
                    sides_count[side] += 1
                except KeyError:
                    sides_count[side] = 1

            game_data[game]["games"].append(tg)

        if over_under_count:
            over_under_avg = round(sum(over_under_count) / len(over_under_count), 2)
        else:
            over_under_avg = 0

        sides_count_list = [[side, sides_count[side]] for side in sides_count]

        if len(sides_count_list) == 1:
            sides_count_list.append([None, None])
            # return dump(sides_count_list)

        game_data[game]["summary"] = {
            "over_under_count": over_under_count,
            "over_under_avg": over_under_avg,
            "sides_count": sides_count_list
        }

    # return dump(game_data)

    return render_template('index.html', data=game_data, date=todays_date)


@app.route("/run")
def run():
    dataset = scrape_data()

    for data in dataset:
        existing = client["MLB"]["covers"].find_one({
            "profile": data["profile"],
            "date": data["date"],
            "game": data["game"],
        })

        if not existing:
            client["MLB"]["covers"].insert_one(data)

    return "Success"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
