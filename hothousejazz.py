#!/usr/bin/env python3
from datetime import datetime, timedelta
import json
from string import Template
import re
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode
from tidal import Tidal


def fetch_calendar_json(date):
    url = "https://www.hothousejazz.com/calendar-filter"
    data = {"start_date": date, "selected_date": date}
    print("fetching url %s date %s" % (url, date))
    req = Request(url, data=urlencode(data).encode())
    req.add_header("user-agent", "Mozilla")
    resp = json.load(urlopen(req))
    return resp


def fetch_calendar_html_old(date):
    print("fetching events for %s ..." % date)
    url = f"https://www.hothousejazz.com/generateCalender.php?what=event&date={date}&sort_by=&sort_id=&search_val=&venue_id=0&order_by=2"
    print("url: %s" % url)
    req = Request(url)
    req.add_header("user-agent", "Mozilla")
    try:
        resp = urlopen(req)
        html = resp.read().decode()
        return html
    except HTTPError as ex:
        print("HTTPError: %s" % ex.read())


def match_to_event(html):
    if not html:
        return

    return {
        "date": get_date_from_html(html),
        "artist": get_artist_from_html(html),
        "time": get_time_from_html(html),
        # "city": get_city_from_html(html),
        "venue": get_venue_from_html(html),
        "url": get_url_from_html(html),
    }


def get_url_from_html(html):
    pattern = r"event_detail\/\d+"
    return f"https://www.hothousejazz.com/{re.search(pattern, html).group(0)}"


def get_date_from_html(html):
    pattern = r"\<span\>(.*)</span>"
    month_day = re.search(pattern, html).group(1)
    date = re.search(r"\<h5>(\d+) <span>", html).group(1)

    return f"{date} {month_day}"


def get_artist_from_html(html):
    pattern = r"<h6>(.*)</h6>"

    return re.search(pattern, html).group(1).strip()


def get_time_from_html(html):
    pattern = r'<p class="text-left">(.*?)</p>'
    return re.search(pattern, html).group(1).strip()


def get_city_from_html(html):
    pattern = r'fa-map-marker-alt"></i>(.*?)</p><p>'
    return re.search(pattern, html).group(1).strip()


def get_venue_from_html(html):
    pattern = r'<p><i class="fas fa-map-marker-alt"></i>(.*?)</p>\s*<p>'
    return re.search(pattern, html).group(1).strip()


def html_to_events(html):
    pattern = r"(<div class=.*?)\n\s+\n"
    matches = re.findall(pattern, html, re.DOTALL)
    events = list(filter(lambda x: x, map(match_to_event, matches)))
    print("found %d events" % len(events))
    return events


def get_dates(days):
    """get today + 30 days"""
    today = datetime.today()
    dates = [today + timedelta(days=td) for td in range(days)]
    return [d.strftime("%Y-%m-%d") for d in dates]


def get_calendar(days=30):
    print("fetching %d days ..." % days)
    dates = get_dates(days=days)

    json_list = map(fetch_calendar_json, dates)
    html_list = [i["data"] for i in json_list]

    all_events = []
    for html in html_list:
        events = html_to_events(html)
        all_events.extend(events)

    return all_events


def fix_artist_name(artist):
    replacements = [" Qrt", " Qnt", " Trio", " Gp"]
    for rep in replacements:
        if artist.endswith(rep):
            artist = artist.replace(rep, "")
    return artist


def check_popularity(events):
    tidal = Tidal()

    # with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    #     # pass account_id and check_logs to check_account function
    #     results = list(
    #         executor.map(
    #             lambda a: tidal.search_artist(artist),
    #             [fix_artist_name(event["artist"]) for event in events],
    #         )
    #     )
    for event in events:
        result = tidal.search_artist(artist=fix_artist_name(event["artist"]))
        if not result["items"]:
            continue
        first_result = result["items"][0]
        if first_result["name"].lower() != event["artist"].lower():
            continue
        event["popularity"] = first_result["popularity"]
        print(event)
    return events


def events_to_html(events):
    html = ""
    template_string = """\n<div>
    <h3>$date</h3>
    <h3>$artist$starred</h3>
    <h4>$venue</h4>
    </div>"""
    template = Template(template_string)
    for event in events:
        if event.get("popularity", 0) >= 25:
            event["starred"] = f" - POPULAR [{event['popularity']}]"
        else:
            event["starred"] = ""
        html += template.substitute(event)
    return html


def save_html(events):
    events_html = events_to_html(events)
    html = f"""
<html>
<head>
<title>Hot House Jazz Events</title>
</head>
<body>
<h1>Hot House Jazz Events</h1>
{events_html}
</body>
</html>
"""
    print("saving index.html")
    with open("public/index.html", "w") as f:
        f.write(html)


def _test_html_to_events():
    with open("_events.html") as f:
        html = f.read()

    events = html_to_events(html)
    print(events)


def main():
    print("starting...")
    events = get_calendar(25)
    events = check_popularity(events)
    save_html(events)
    return


if __name__ == "__main__":
    main()
