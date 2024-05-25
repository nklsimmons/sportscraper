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
    # https://contests.covers.com/kingofcovers/cdd9afbe-a974-418f-a86f-b13f013c3e1d
    base_url = "https://contests.covers.com"
    url = "/kingofcovers/cdd9afbe-a974-418f-a86f-b13f013c3e1d"

    with urlopen(base_url + url) as main_page:
        html_bytes = main_page.read()

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

    data = []

    for row in rows:

        tds = row.find_all("td")

        status = tds[6].text.strip()
        if status != "Pending":
            continue

        profile_name = tds[1].text.strip()
        profile_link = tds[5].find('a')['href']

        with urlopen(base_url + profile_link) as profile_page:
            profile_html_bytes = profile_page.read()

        profile_html = profile_html_bytes.decode("utf-8")

        profile_soup = BeautifulSoup(profile_html, "html.parser")

        picks_table = profile_soup.find_all("table", class_="cmg_contests_pendingpicks")[-1]

        date_today = picks_table.find_previous_sibling("h3").text

        picks_trs = picks_table.find_all("tr")

        for pick_tr in picks_trs:

            picks_tds = pick_tr.find_all("td")

            data.append({
                "profile": profile_name,
                "date": date_today,
                "game": ' - '.join(clean_text(picks_tds[0].text)),
                "time": ''.join(clean_text(picks_tds[2].text)),
                "pick": parse_picks(clean_text(picks_tds[3].text)),
                # "units": clean_text(picks_tds[4].text),
            })

    return data


def clean_text(text):
    text_arr = text.strip().split("\n")
    cleaned_text_arr = [t.strip() for t in text_arr]
    return list(filter(lambda t: t, cleaned_text_arr))


def parse_picks(picks):
    over_under = None
    over_under_value = None
    side = None
    side_value = None

    for pick in picks:
        p_arr = pick.split()
        if p_arr[0] == 'Over' or p_arr[0] == 'Under':
            over_under = p_arr[0]
            over_under_value = p_arr[1]
        else:
            side = p_arr[0]
            side_value = p_arr[1]

    return {
        "O/U": (over_under, over_under_value) if over_under else None,
        "Side": (side, side_value) if side else None
    }
