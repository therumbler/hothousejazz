#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import logging
import os
import re
from string import Template
import sys
import time
from uuid import uuid4
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import urlencode

from tidal import Tidal

logger = logging.getLogger("hothousejazz")


tidal = Tidal()


def fetch_calendar_json(date):
    url = "https://www.hothousejazz.com/calendar-filter"
    data = {"start_date": date, "selected_date": date}
    logger.debug("fetching url %s date %s", url, date)
    req = Request(url, data=urlencode(data).encode())
    req.add_header("user-agent", "Mozilla")
    resp = json.load(urlopen(req))
    return resp


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
    try:
        path = re.search(pattern, html).group(0)
    except AttributeError as ex:
        logger.error("AttributeError for pattern %s", pattern)
        with open("_temp_html.html", "w") as f:
            f.write(html)
        raise
    return f"https://www.hothousejazz.com/{path}"


def get_date_from_html(html):
    pattern = r"\<span\>(.*?)</span>"
    try:
        month_day = re.search(pattern, html, re.DOTALL).group(1)
    except AttributeError as ex:
        logger.error("AttributeError for month_day")
        with open("_temp_html.html", "w") as f:
            f.write(html)
        raise
    try:
        date = re.search(r'"al-date">(\d{2}?)\s+', html).group(1)
        # date = re.search(r"\<h5.*>(\d+)\s+<span>", html).group(1)
    except AttributeError as ex:
        logger.error("AttributeError for date")
        with open("_temp_html.html", "w", encoding="utf-8") as f:
            f.write(html)
        raise
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
    pattern = r'target="_blank">\s*(.*?)\s+</a>'

    venue = re.search(pattern, html, re.DOTALL).group(1).strip()
    pattern = r"<p>(.*?)</p>"
    neighbourhood = re.search(pattern, html).group(1)
    return f"{venue}, {neighbourhood}"


def html_to_events(html):
    pattern = r'<div class="calendar-box">[.\s\S]*?\n\s{9}</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    if len(matches) == 0:
        logger.error("html_to_events regex pattern found 0 events")
    events = list(filter(lambda x: x, map(match_to_event, matches)))
    return events


def get_dates(days):
    """get today + 30 days"""
    today = datetime.today()
    dates = [today + timedelta(days=td) for td in range(days)]
    return [d.strftime("%Y-%m-%d") for d in dates]


def get_calendar(days=30):
    logger.info("fetching %d days ...", days)
    dates = get_dates(days=days)

    with ThreadPoolExecutor() as executor:
        logger.info("using %d workers to fetch calendars", executor._max_workers)
        json_list = list(executor.map(fetch_calendar_json, dates))

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


def _event_to_event_popularity(event):
    fixed_artist_name = fix_artist_name(event["artist"])
    result = tidal.search_artist(artist_name=fixed_artist_name)
    if not result["items"]:
        return event
    first_result = result["items"][0]
    if first_result["name"].lower() != fixed_artist_name.lower():
        return event
    event["popularity"] = first_result["popularity"]
    return event


def check_popularity(events):
    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        logger.info("using %d workers to fetch popularity", executor._max_workers)
        results = list(executor.map(_event_to_event_popularity, events))

    end_time = time.time()
    logger.info(
        "Fetched %d results in %d seconds", len(events), (end_time - start_time)
    )
    return results


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
    with open("./templates/index.html") as f:
        template_string = f.read()
    template = Template(template_string)
    html = template.substitute(events_html=events_html)

    logger.info("saving index.html")
    with open("public/index.html", "w") as f:
        f.write(html)


def _test_html_to_events():
    with open("_temp_html.html") as f:
        html = f.read()

    events = html_to_events(html)
    print(events)


def main():
    """let's do the thing!"""
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=LOG_LEVEL, stream=sys.stdout)

    logger.info("starting...")
    events = get_calendar(25)
    events = check_popularity(events)
    if len(events) == 0:
        logger.error("no events found. Check regex")
        sys.exit(1)
    save_html(events)


if __name__ == "__main__":
    main()
