#!/usr/bin/env python
from dotenv import load_dotenv
from functions import dump, filter_duplicates, date_string_to_date
import os

from flask import Flask, render_template
from pymongo import MongoClient
from datetime import datetime

from app import scrape_data


load_dotenv()

MONGODB_CONTAINER = os.getenv('MONGODB_CONTAINER')

app = Flask(__name__)
client = MongoClient(f"mongodb://{MONGODB_CONTAINER}")

def get_last_update():
    last_update_string = client["MLB"]["update_record"].find({}, {"datetime": 1}).sort({"datetime": -1})[0]["datetime"]
    last_update = datetime.strptime(last_update_string, "%Y-%m-%d %H:%M:%S.%f")
    return last_update


@app.route("/")
def index():
    entries = client["MLB"]["covers"].find({}, {"date": 1})

    unique_dates = filter_duplicates([e["date"] for e in entries])

    dates_list = []

    for date in unique_dates:
        dates_list.append({
            "name": date,
            "date": str(date_string_to_date(date))
        })

    dates_list.sort(reverse=True, key=lambda d : d["date"])

    now = datetime.now()
    time_since_last_update = now - get_last_update()
    mins_since_last_update = int(time_since_last_update.total_seconds() / 60)

    return render_template('index.html',
                           latest=dates_list[0],
                           dates=dates_list[1:],
                           mins_since_last_update=mins_since_last_update)


@app.route("/picks/<date>")
def showDate(date):
    picks_datetime = datetime.strptime(date, "%Y-%m-%d")
    date_str = picks_datetime.strftime("%A, %B %-d")

    games = set()

    # Get all relevant dates
    todays = client["MLB"]["covers"].find({"date": date_str})
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
                "date": date_str
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

        game_data[game]["summary"] = {
            "over_under_count": over_under_count,
            "over_under_avg": over_under_avg,
            "sides_count": sides_count_list
        }

    now = datetime.now()
    time_since_last_update = now - get_last_update()
    mins_since_last_update = int(time_since_last_update.total_seconds() / 60)

    return render_template('show.html',
                           data=game_data,
                           date=date_str,
                           mins_since_last_update=mins_since_last_update)


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

    client["MLB"]["update_record"].insert_one({
        "datetime": str(datetime.now())
    })

    return "Success"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
