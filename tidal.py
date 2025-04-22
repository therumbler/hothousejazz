from functools import lru_cache
import json
import logging
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

logger = logging.getLogger(__name__)


class Tidal:
    base_url = "https://api.tidalhifi.com/v1"

    def _fetch(self, endpoint: str, **params) -> dict:
        params = self._add_default_params(params)
        url = f"{self.base_url}/{endpoint}?{urlencode(params)}"
        logger.debug("loading url %s" % url)
        try:
            with urlopen(url) as resp:
                return json.load(urlopen(url))
        except HTTPError as ex:
            logger.error("HTTP Error %d: error fetching %s", ex.code, url)
            return {}

    def _add_default_params(self, params: dict) -> dict:
        if "token" not in params:
            params["token"] = TOKEN
        if "countryCode" not in params:
            params["countryCode"] = "US"
        return params

    @lru_cache
    def search_artist(self, artist_name):
        """search tidal by artist name name"""
        url = f"https://api.tidalhifi.com/v1/search?types=artists&token={TOKEN}&countryCode=US&query={quote(artist_name)}"

        logger.debug("loading url %s", url)
        resp = json.load(urlopen(url))["artists"]
        logger.debug("fetched %d artists", len(resp))
        return resp

    def search_all(self, query, **params):
        endpoint = "search"
        limit = 100
        if not params:
            params = {"types": "tracks", "query": quote(query), "limit": limit}
        if "query" not in params:
            params["query"] = query
        resp = self._fetch(endpoint=endpoint, **params)
        total_number_of_tracks = resp["tracks"]["totalNumberOfItems"]
        offset = resp["tracks"]["offset"]
        while len(resp["tracks"]["items"]) < total_number_of_tracks:
            offset += limit
            params["offset"] = offset
            logger.debug("offset: %d", offset)
            resp1 = self._fetch(endpoint, **params)
            resp["tracks"]["items"].extend(resp1["tracks"]["items"])
        return resp

    @lru_cache
    def search(self, query, **params):
        """use the search endpoint"""
        # url = f"https://api.tidalhifi.com/v1/search?types=artists&token={TOKEN}&countryCode=US&query={quote(artist)}"
        endpoint = "search"
        if not params:
            params = {"types": "artists", "query": quote(query)}
        if "query" not in params:
            params["query"] = query
        return self._fetch(endpoint=endpoint, **params)

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
        endpoint = f"albums/{album_id}"
        return self._fetch(endpoint)


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
    import os

    tidal = Tidal()
    log_level = os.environ.get("LOG_LEVEL", "DEBUG")
    logging.basicConfig(level=log_level)
    # album_id = 202990883
    # album = tidal.get_album(album_id)
    # url = _get_album_image_url(album)
    # print("url", url)
    query = "oscar peterson"
    resp = tidal.search_all(query=query, types="TRACKS", limit=100)
    for item in resp["tracks"]["items"]:
        if "HIRES_LOSSLESS" not in item["mediaMetadata"]["tags"]:
            # if item["audioQuality"] in ("HIGH"):
            continue
        artist_names = [a["name"] for a in item["artists"]]
        logger.info(
            "%s — %s - %s ",
            " & ".join(artist_names),
            item["title"],
            item["album"]["title"],
        )
    return

    result = tidal.search_artist(artist_name="u2")
    print(result)
    return
    mix_id = "00900ca36f4ef5a00a49d7c6192b3f"
    mix_id = "0098c3e1f3d46c7e4fbaba02f012a7"  # benji 2023
    mix = tidal.get_mix(mix_id)
    # print(mix)
    resp = get_year_count_from_mix(mix)
    # resp = tidal.search_artist(artist_name="jamile")

    print(resp)
    # results = tidal.search_artist(artist_name="Eddie Henderson")
    # print(results)


if __name__ == "__main__":
    main()
