#!/usr/bin/env python3

# Copyright (c) Dom Rodriguez 2020
# Licensed under the Apache License 2.0

import os
import sys
import feedparser
import logging
from os import environ
from feedgen.feed import FeedGenerator

log = None
LOG_LEVEL = environ.get("SR_LOG_LEVEL", "ERROR")
fg = None
FEED_OUT_PATH = None
FEED_OUT_TYPE = None
FEED_LIST_PATH = None
FEEDS = []



def setup_logging() -> None:
    """
    This function intialises the logger framework.
    """
    global log

    log = logging.getLogger(__name__)
    log.setLevel(LOG_LEVEL)
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(ch)

    return None


def init_feed() -> None:
    """
    This function initialises the RSS feed with the
    correct attributes.
    """
    log.debug("Initialising the output feed...")

    global fg

    try:
        fg = FeedGenerator()
        # Setup [root] feed attributes
        fg.id("https://rss.example.com")
        fg.title("SingleRSS - Combined Feed")
        fg.generator("SingleRSS/v1.0.0")
        fg.link(href="https://rss.example.com", rel="self")
        fg.subtitle("Combined feed for RSS feeds")
        fg.language('en')
    except:
        log.error("Error initialising the output feed!")
        sys.exit(1)

    log.debug("Output feed initialised!")

    return None


def parse_feed(url) -> feedparser.FeedParserDict:
    log.debug("Parsing input RSS/Atom feed..")

    feed = feedparser.parse(url)

    if feed.bozo:
        log.warning("Parsing RSS/Atom feed encountered an error: {err}".format(err=str(feed.bozo_exception)))
        return feed # return anyway, it may still be partially readable...

    if feed is None:
        log.warning("No value from feedparser. Unusual error, please report.")
        return None

    return feed


def main():
    feeds = None
    with open(FEED_LIST_PATH, "r") as infile:
        feeds = infile.read().splitlines()

    for feed in feeds:
        FEEDS.append(feed)

    for feed in FEEDS:
        rss = parse_feed(feed)

        if not rss:
            log.warning("Error detected during feed parsing process. Feed: {feed}".format(feed=feed))
            continue


        log.info("Processing feed: {feed}".format(feed=feed))
        entries = rss.get("entries")

        for entry in entries:
            fe = fg.add_entry()

            try:
                fe.id(entry["id"])
            except:
                # Definitely weird...
                fe.id("about:blank")

            try:
                fe.title(entry["title"])
            except:
                # OK, this is a definititive malformed feed entry.
                fe.title("Unspecified")

            try:
                fe.link(href=entry["link"])
            except:
                # When we have a empty link attribute, this isn't ideal
                # to set a default value.. :/
                fe.link(href='about:blank')

            try:
                if entry["sources"]["authors"]:
                    for author in entry["sources"]["authors"]:
                        fe.author(author)
                elif entry["authors"]:
                    for author in entry["authors"]:
                        fe.author(author)
            except:
                # Sometimes we don't have ANY author attributes, so we
                # have to set a dummy attribute.
                fe.author({"name": "Unspecified",
                           "email": "unspecified@example.com"})

            try:
                if entry["summary"]:
                    fe.summary(entry["summary"])
                    fe.description(entry["summary"])
                elif entry["description"]:
                    fe.description(entry["description"])
                    fe.summary(entry["description"])
                    fe.content(entry["description"])
            except:
                # Sometimes feeds don't provide a summary OR description, so we
                # have to set an empty value.
                # This is pretty useless for a feed, so hopefully we
                # don't have to do it often!
                fe.description("Unspecified")
                fe.summary("Unspecified")

            try:
                if entry["published"]:
                    try:
                        fe.published(entry["published"])
                        fe.updated(entry["published"])
                    except:
                        fe.published("1970-01-01T00:00:00+00:00")
                        fe.updated("1970-01-01T00:00:00+00:00")
                        continue
            except:
                # Sometimes feeds don't even provide a publish date, so we default to
                # the start date &time of the Unix epoch.
                fe.published("1970-01-01T00:00:00+00:00")
                fe.updated("1970-01-01T00:00:00+00:00")


if __name__ == "__main__":
    setup_logging()

    log.debug("Starting up..")

    try:
        # Configuration is specified with environemnt variables.
        log.debug("Assignment attempt: SINGLERSS_FEED_OUT_PATH")
        FEED_OUT_PATH = os.environ["SINGLERSS_FEED_OUT_PATH"]
    except KeyError:
        log.error("`SINGLERSS_FEED_OUT_PATH` variable missing, can't run.")
        sys.exit(1)

    try:
        FEED_LIST_PATH = os.environ["SINGLERSS_FEED_LIST_PATH"]
    except:
        log.error("`SINGLERSS_FEED_LIST_PATH` variable missing, can't run.")
        sys.exit(1)

    try:
        FEED_OUT_TYPE = os.environ["SINGLERSS_FEED_OUT_TYPE"]
    except KeyError:
        log.error("`SINGLERSS_FEED_OUT_TYPE` variable missing, can't run.")
        sys.exit(1)

    init_feed()

    main()

    if FEED_OUT_TYPE == "stdout":
        log.debug("stdout output specified, outputting to stdout.")
        print(fg.rss_str().decode('utf-8'))
    elif FEED_OUT_TYPE == "file":
        log.debug("File output specified, outputting to specified file..")
        fg.rss_file(FEED_OUT_PATH)
    else:
        log.error("Unknown type of output preference, cannot run.")
        sys.exit(1)
