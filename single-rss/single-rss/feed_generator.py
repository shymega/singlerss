from feedgen.feed import FeedGenerator as FeedGeneratorExt


class FeedGenerator(object):
    __feedgen: FeedGeneratorExt

    def __init__(self, feeds: dict, metadata: dict):
        self.__feeds = feeds
        self.__metadata = metadata
