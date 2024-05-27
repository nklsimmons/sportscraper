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
MONGODB_USER = os.getenv('MONGODB_USER')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')

app = Flask(__name__)
client = MongoClient(f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_CONTAINER}")

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

    days = client["MLB"]["covers"].find({"date": date_str})
    for t in days:
        games.add(t["game"])

    game_data = dict()
    for game in games:
        try:
            game_data[game]
        except KeyError:
            game_data[game] = {"games": [], "summary": dict()}

        days_games = client["MLB"]["covers"].find(
            {
                "game": game,
                "date": date_str
            }, {"_id": 0})

        over_under_count = dict()
        sides_count = dict()

        for tg in days_games:
            game_time = tg["time"]

            if tg["pick"].get("O/U"):

                over_under_value = float(tg["pick"].get("O/U")[1])
                if tg["pick"].get("O/U")[0] == "Under":
                    over_under_value = over_under_value * -1

                try:
                    over_under_count[str(over_under_value)] += 1
                except KeyError:
                    over_under_count[str(over_under_value)] = 1

            if tg["pick"].get("Side"):
                side = tg["pick"].get("Side")[0]

                try:
                    sides_count[side] += 1
                except KeyError:
                    sides_count[side] = 1

            game_data[game]["games"].append(tg)

        over_under_sum = {}

        if over_under_count:
            ou_count = sum(over_under_count[n] for n in over_under_count)
            ou_sum = sum(over_under_count[n] * float(n) for n in over_under_count)
            over_under_avg = ou_sum / ou_count
        else:
            over_under_avg = 0

        sides_count_list = [[side, sides_count[side]] for side in sides_count]

        if len(sides_count_list) == 1:
            sides_count_list.append([0, 0])

        over_under_sum = {"over": 0, "under": 0}

        for v in over_under_count:
            if float(v) < 0:
                over_under_sum["under"] += over_under_count[v]
            if float(v) > 0:
                over_under_sum["over"] += over_under_count[v]

        game_data[game]["summary"] = {
            "over_under_sum": over_under_sum,
            "over_under_count": over_under_count,
            "over_under_avg": over_under_avg,
            "sides_count": sides_count_list,
            "time": game_time
        }

    # I am too fucking tired to do a proper refactor so this will have to do for now
    game_data_list = []
    for game in game_data:
        game_data_list.append({
            "name": game,
            "time": game_data[game]["games"][0]["time"],
            "picks": game_data[game]["games"],
            "summary": game_data[game]["summary"],
        })
    game_data_list.sort(key=lambda g : g["time"])

    now = datetime.now()
    time_since_last_update = now - get_last_update()
    mins_since_last_update = int(time_since_last_update.total_seconds() / 60)

    return render_template('show.html',
                           data=game_data_list,
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
