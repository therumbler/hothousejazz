from functools import lru_cache
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import quote, urlencode

# TOKEN = y3Ab6MUg5bjjofvu
# TOKEN = "qe5mgUGPtIfbgN574ngS74Sd1OmKIfvcLx7e28Yk"
TOKEN = "CzET4vdadNUFQ5JU"
# TOKEN = "M6ztoSvmny6alVCD"
# TOKEN = "Y40WSvVnnG0ql0L0"
# TOKEN = "NIh99tUmaAyLNmEA"
# TOKEN = "jdDuod31BUA6qXXq"


class Tidal:
    def _fetch(self, url):
        # print("loading url %s" % url)
        return json.load(urlopen(url))

    @lru_cache
    def search_artist(self, artist):
        url = f"https://api.tidalhifi.com/v1/search?types=artists&token={TOKEN}&countryCode=US&query={quote(artist)}"
        # print("searching %s" % artist)
        # print("loading url %s" % url)
        return json.load(urlopen(url))["artists"]

    def get_mix(self, mix_id):
        params = {
            "mixId": mix_id,
            "deviceType": "BROWSER",
            "countryCode": "US",
            "token": TOKEN,
        }
        url = f"https://api.tidalhifi.com/v1/pages/mix?{urlencode(params)}"
        # print("fetching %s" % url)
        resp = json.load(urlopen(url))
        # print("fetched")
        return resp

    def get_album(self, album_id):
        url = f"https://api.tidalhifi.com/v1/albums/{album_id}?countryCode=US&token={TOKEN}"
        return self._fetch(url)


def get_year_count_from_mix(mix):
    years = {}
    decades = {}
    for row in mix["rows"]:
        if row["modules"][0]["type"] != "TRACK_LIST":
            continue
        items = row["modules"][0]["pagedList"]["items"]

    for item in items:
        item_year = item["album"]["releaseDate"][:4]
        item_decade = item["album"]["releaseDate"][:3] + "0s"
        if item_year in years:
            years[item_year] += 1
        else:
            years[item_year] = 1
        if item_decade in decades:
            decades[item_decade] += 1
        else:
            decades[item_decade] = 1
    return {"years": years, "decades": decades}


def _get_album_image_url(album, width=1280, height=1280):
    """get the url for album artwork"""
    # template = "http://images.osl.wimpmusic.com/im/im?w={}&h={}&albumid={}"
    # artwork_url = template.format(width, height, album["id"])
    artwork_url = "https://resources.wimpmusic.com/images/%s/1280x1280.jpg" % album[
        "cover"
    ].replace("-", "/")
    return artwork_url


def main():
    tidal = Tidal()
    album_id = 202990883
    album = tidal.get_album(album_id)
    url = _get_album_image_url(album)
    print("url", url)
    return

    result = tidal.search_artist(artist="u2")
    print(result)
    return
    mix_id = "00900ca36f4ef5a00a49d7c6192b3f"
    mix_id = "0098c3e1f3d46c7e4fbaba02f012a7"  # benji 2023
    mix = tidal.get_mix(mix_id)
    # print(mix)
    resp = get_year_count_from_mix(mix)
    # resp = tidal.search_artist(artist="jamile")

    print(resp)
    # results = tidal.search_artist(artist="Eddie Henderson")
    # print(results)


if __name__ == "__main__":
    main()
