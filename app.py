from pprint import pprint
from urllib.request import urlopen
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from functions import dump


def scrape_data(league):

    if league not in ("MLB", "WNBA"):
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


def get_money_leaders_picks(league, **kwargs):

    if league not in ("MLB", "WNBA", "NCAAF", "NBA", "NFL"):
        raise Exception("League is empty or not supported")

    # https://contests.covers.com/consensus/pickleaders/mlb?totalPicks=500&orderBy=Units&orderPickBy=StraightUp

    base_url = "https://contests.covers.com"
    url = f"/consensus/pickleaders/{league.lower()}?"

    query = urlencode({
        "totalPicks": kwargs.get("totalPicks", "500"),
        "orderBy": kwargs.get("orderBy", "Units"),
        "orderPickBy": kwargs.get("orderPickBy"),
    })
    altTextToSearch = f"{league.lower()} Pending Picks"

    with urlopen(base_url + url + query) as main_page:
        html_bytes = main_page.read()
        html = html_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

    """
    Get day's leaders from leaderboard
    """

    try:
        leaderboard_table = soup.find_all("table", class_="leaderboard")[0]
    except IndexError:
        return []

    limit = kwargs.get("limit", 10)
    leaderboard_rows = leaderboard_table.find("tbody").find_all("tr")[0:limit]

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

        has_pending_picks = leaderboard_tds[1].find("img", alt=altTextToSearch) is not None
        l["pending_picks_url"] = leaderboard_tds[1].find("img", alt=altTextToSearch).parent["href"] if has_pending_picks else None

        leaders.append(l)

    """
    Get picks from leaders
    """

    for leader in leaders:
        if leader["pending_picks_url"] is None:
            continue

        picks_url = leader["pending_picks_url"].replace(" ", "%20")

        with urlopen(picks_url) as picks_page:
            html_bytes = picks_page.read()
            html = html_bytes.decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

        leader_picks = []

        pick_tables = soup.find_all("table", class_="cmg_contests_pendingpicks")

        for pick_table in pick_tables:

            picks_rows = pick_table.find("tbody").find_all("tr")
            pick_date = pick_table.find_previous_sibling("h3").text

            for picks_row in picks_rows:
                picks_tds = picks_row.find_all("td")

                # Skip games in progress
                if picks_tds[1].text.strip() != "-\n\n-":
                    continue

                game_string = picks_tds[0].text.strip()
                game = ' - '.join(filter(lambda x : x, (g.strip() for g in game_string.split('\n'))))

                # O/Us and Sides
                pick = picks_tds[3].text.strip()

                # Wtf is this for
                # if pick.find('\n') != -1:
                #     continue

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
                    "date": pick_date,
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


class DebugError(Exception):
    def __init__(self, data):
        self.data = data
