#!/usr/bin/env python3
from datetime import datetime, timedelta
from string import Template
import re
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from tidal import Tidal


def fetch_calendar_html(date):
    print("fetching events for %s ..." % date)
    url = f"https://www.hothousejazz.com/generateCalender.php?what=event&date={date}&sort_by=&sort_id=&search_val=&venue_id=0&order_by=2"
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
    # print(html)
    return {
        "date": get_date_from_html(html),
        "artist": get_artist_from_html(html),
        "time": get_time_from_html(html),
        "city": get_city_from_html(html),
        "venue": get_venue_from_html(html),
        "url": get_url_from_html(html),
    }


def get_url_from_html(html):
    pattern = r"event_detail\.php\?eid=\d+"
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
    pattern = r'</p><p><i class="fas fa-map-marker-alt"></i>(.*?)</p>\s*<p>'
    return re.search(pattern, html).group(1).strip()


def html_to_events(html):
    pattern = r"(<div class=.*)\n\n"
    matches = re.findall(pattern, html)

    events = list(filter(lambda x: x, map(match_to_event, matches)))
    print("found %d events" % len(events))
    return events


def get_dates(days):
    """get today + 30 days"""
    today = datetime.today()
    dates = [today + timedelta(days=td) for td in range(days)]
    return [d.strftime("%Y-%m-%d") for d in dates]


def get_calendar(days=30):
    # url = "https://www.hothousejazz.com/generateCalender.php?what=event&date=2022-9-8&sort_by=&sort_id=&search_val=&venue_id=0&order_by=2"
    dates = get_dates(days=days)
    html_list = map(fetch_calendar_html, dates)
    all_events = []
    for html in html_list:

        # html = fetch_calendar_html()
        # print(html)
        events = html_to_events(html)
        all_events.extend(events)

    return all_events


def check_popularity(events):
    tidal = Tidal()
    for event in events:
        result = tidal.search_artist(artist=event["artist"])
        if not result["items"]:
            continue
        event["popularity"] = result["items"][0]["popularity"]
        print(event)
    return events


def events_to_html(events):
    html = ""
    template_string = """\n<div>
    <h3>$date</h3>
    <h3>$artist</h3>
    <h4>$venue</h4>
    </div>"""
    template = Template(template_string)
    for event in events:
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


def main():
    events = get_calendar(1)
    # print(events)
    events = check_popularity(events)
    save_html(events)
    return


if __name__ == "__main__":
    main()
