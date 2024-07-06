from pprint import pprint
from urllib.request import urlopen
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from functions import dump

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

LEAGUES = ("MLB", "WNBA")


def scrape_data(league):

    if league not in LEAGUES:
        raise Exception("League is empty or not supported")

    # MLB
    # https://contests.covers.com/kingofcovers/cdd9afbe-a974-418f-a86f-b13f013c3e1d

    # WNBA
    # https://contests.covers.com/kingofcovers/a84a7067-afcc-47b1-88c6-b16f00d2e70d

    base_url = "https://contests.covers.com"

    if league == "MLB":
        url = "/kingofcovers/cdd9afbe-a974-418f-a86f-b13f013c3e1d"
    if league == "WNBA":
        url = "/kingofcovers/a84a7067-afcc-47b1-88c6-b16f00d2e70d"

    with urlopen(base_url + url) as main_page:
        html_bytes = main_page.read()

    html = html_bytes.decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find_all("table", class_="leaderboard")[0]

    rows = table.find("tbody").find_all("tr")

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
            })

    return data


def scrape_data_v2(league):

    if league not in ("MLB"):
        raise Exception("League is empty or not supported")

    # MLB
    # https://contests.covers.com/consensus/pickleaders/mlb?totalPicks=500&orderBy=Units&orderPickBy=StraightUp

    # WNBA

    base_url = "https://contests.covers.com"

    if league == "MLB":
        url = "/consensus/pickleaders/mlb?"
        query = urlencode({
            "totalPicks": "500",
            "orderBy": "Units",
            "orderPickBy": "StraightUp",
        })
    if league == "WNBA":
        pass
        # url = "/kingofcovers/a84a7067-afcc-47b1-88c6-b16f00d2e70d"

    with urlopen(base_url + url + query) as main_page:
        html_bytes = main_page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

    """
    Get day's leaders from leaderboard
    """

    leaderboard_table = soup.find_all("table", class_="leaderboard")[0]
    leaderboard_rows = leaderboard_table.find("tbody").find_all("tr")

    leaders = []
    for leaderboard_row in leaderboard_rows:
        leaderboard_tds = leaderboard_row.find_all("td")

        l = {
            "rank": leaderboard_tds[0].text.strip(),
            "user": leaderboard_tds[1].text.strip(),
            "units": leaderboard_tds[2].text.strip(),
            "sides": leaderboard_tds[3].text.strip(),
            "diff": leaderboard_tds[4].text.strip(),
            "win_rate": leaderboard_tds[5].text.strip(),
        }

        has_pending_picks = leaderboard_tds[1].find("img", alt="mlb Pending Picks") is not None
        l["pending_picks_url"] = leaderboard_tds[1].find("img", alt="mlb Pending Picks").parent["href"] if has_pending_picks else None

        leaders.append(l)

    """
    Get picks from leaders
    """

    for leader in leaders:
        if leader["pending_picks_url"] is None:
            continue

        with urlopen(leader["pending_picks_url"]) as picks_page:
            html_bytes = picks_page.read()
            html = html_bytes.decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

        date = soup.find("div", class_="main_bar").find("h3").text

        picks_table = soup.find("table", class_="cmg_contests_pendingpicks")
        picks_rows = picks_table.find("tbody").find_all("tr")

        leader_picks = []
        for picks_row in picks_rows:
            picks_tds = picks_row.find_all("td")

            # Skip games in progress
            if picks_tds[1].text.strip() != "-\n\n-":
                continue

            game_string = picks_tds[0].text.strip()
            game = ' - '.join(filter(lambda x : x, (g.strip() for g in game_string.split('\n'))))

            # O/Us and Sides
            pick = picks_tds[3].text.strip()

            if pick.find('\n') != -1:
                continue

            parsed_picks = list(filter(lambda x : x, (p.strip() for p in pick.split('\n'))))

            picks = {}
            if len(parsed_picks) > 1:
                picks["sides"] = parsed_picks[0]
                picks["ou"] = parsed_picks[1]
            elif parsed_picks[0].find("Over") != -1 or parsed_picks[0].find("Under") != -1:
                picks["sides"] = None
                picks["ou"] = parsed_picks[0]
            else:
                picks["sides"] = parsed_picks[0]
                picks["ou"] = None

            leader_pick = {
                "date": date,
                "game": game,
                # "score": picks_tds[1].text.strip(),
                "status": picks_tds[2].text.strip(),
                "pick": picks,
            }
            leader_picks.append(leader_pick)

        leader["picks"] = leader_picks

    return leaders


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
