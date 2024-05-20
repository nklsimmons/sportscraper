from pprint import pprint
from urllib.request import urlopen
from bs4 import BeautifulSoup

"""
"REGULAR SEASON" TAB
Top 10 members will get their "today" pending picks exported.
I want to know the consensus picks on those 10 members.

example:

User:  TJJohnson03 - PHI, MIL OVER 8.0, ETC, ETC
User:  fishercz- PHI, ETC, ETC
User: pstro- PHI, ETC, ETC
User: simoncald - PHI, ETC, ETC
User: CNOTES - MIL OVER 8.0 ETC, ETC
User: ETC, ETC
User: ETC, ETC
User: ETC, ETC
User: ETC, ETC
User: ETC, ETC

REPORT : SUM = (6) PHI PICKS to (3) LA ANGELS PICKS
(2) MIL OVER 8.0 to (0) MIL UNDER 8.0

See JPG attached for the numbers I ran this morning manually. It looks like the picks do change throughout the day, so maybe a cron is run every 30 min or something.
The highlighted yellow would be the consensus picks for the day. AW=away team, HOM=home team, fyi.

Things to note:
Not all users pick all games, not all users make all picks, some only do over and under, some only do sides. We would eventually add other sports, but let's stick with MLB for now.


10 users have picks for each game
Check their picks on their profiles
Summarize/average the total picks

That's right. The over under just report the average total.
Can you also report average line total for the majority concensus picks?

Clev -130, clev -140 = 2 cleve picks at -135
Under 9, under 8 = 2 clev under picks at 8.5

"""

def get():
    url = "https://contests.covers.com/kingofcovers/cdd9afbe-a974-418f-a86f-b13f013c3e1d"

    with urlopen(url) as page:
        html_bytes = page.read()

    html = html_bytes.decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find_all("table", class_="leaderboard")[0]

    rows = table.find("tbody").find_all("tr")

    data = []

    """
    Grab profile links of top 10 users
    Grab their pending pics
    Add everything to The Array
    Repeat

    Save everything in a MongoDB instance, I guess

    Might as well save everything for history's sake

    Run this every hour ig

    """

    for row in rows:
        tds = row.find_all("td")

        row_data = [td.text.strip() for td in tds]

        new_row = {
            "Rank": row_data[0],
            "Member": row_data[1],
            "W-L-T": row_data[2],
            "%": row_data[3],
            "Units": row_data[4],
            "Status": row_data[6],
        }

        data.append(new_row)

    return data

    # return 'Hello'


# get()