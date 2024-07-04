import json
from datetime import datetime


def dump(v, x=True):
    print(
        str(json.loads(json.dumps(v)))
    )
    if x: exit()

def filter_duplicates(_list):
    _set = set()
    for l in _list:
        _set.add(l)
    return [s for s in _set]

def date_string_to_date(date_string):
    year = datetime.now().year
    date_str = date_string + " " + str(year)
    dt = datetime.strptime(date_str, "%A, %B %d %Y")
    date = str(dt).split(' ')[0]
    return date
