#!/usr/bin/env python
import os

from flask import Flask
from pymongo import MongoClient
from test import get

app = Flask(__name__)
client = MongoClient("mongodb://sportscraper3-mongodb-1")


@app.route("/")
def index():
    # try:
    #     client.admin.command('ismaster')
    # except:
    #     return "Server not available"

    # return 'potato'
    # return 'hello'
    return get()

@app.route("/run")
def run():
    return get()


# @app.route('/')
# def todo():
#     try:
#         client.admin.command('ismaster')
#     except:
#         return "Server not available"
#     return "Hello from the MongoDB client!\n"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ.get("FLASK_SERVER_PORT", 9090), debug=True)
