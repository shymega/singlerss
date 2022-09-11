from feedparser import FeedParserDict, parse


class RSSFeed(object):
    __parsed_dict: FeedParserDict
    __entries: list[dict]

    id: str
    title: str
    link: str
    authors: list[str]
    summary: str
    content:  str
    published: str
    updated: str

    def __init__(self, url: str):
        self.__parsed_dict = parse(url)

    def populate(self):
        rss = self.__parsed_dict
        try:
            self.__entries = rss.get("entries")
        except KeyError:
            pass
