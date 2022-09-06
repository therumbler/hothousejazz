from functools import lru_cache
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import quote


class Tidal:
    @lru_cache
    def search_artist(self, artist):
        url = f"https://api.tidalhifi.com/v1/search?types=artists&token=CzET4vdadNUFQ5JU&countryCode=US&query={quote(artist)}"
        print("searching %s" % artist)
        # print("url %s" % url)
        return json.load(urlopen(url))["artists"]


def main():
    tidal = Tidal()
    results = tidal.search_artist(artist="Eddie Henderson")
    print(results)
    results = tidal.search_artist(artist="Eddie Henderson")
    print(results)


if __name__ == "__main__":
    main()
