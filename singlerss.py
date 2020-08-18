#!/usr/bin/env python3

# Copyright (c) Dom Rodriguez 2020
# Licensed under the Apache License 2.0

import os
import sys
import feedparser
import logging
from feedgen.feed import FeedGenerator

log = None
fg = None
FEED_OUT_PATH = None
FEED_OUT_TYPE = None
FEED_LIST_PATH = None
FEEDS = []


def setup_logging() -> None:
    """
    This function intiialises the logger framework.
    """
    global log

    log = logging.getLogger("singlerss")
    out_handler = logging.StreamHandler(sys.stderr)
    out_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        ))
    log.addHandler(out_handler)
    log.setLevel(logging.ERROR)

    return None


def init_feed() -> None:
    """
    This function initialises the RSS feed with the
    correct attributes.
    """
    log.debug("Initialising the feed...")

    global fg

    try:
        fg = FeedGenerator()
        # Setup [root] feed attributes
        fg.id("https://rss.shymega.org.uk/feed.xml")
        fg.title("SingleRSS - Combined Feed")
        fg.generator("SingleRSS/v1.0.0")
        fg.link(href="https:/rss.shymega.org.uk/feed.xml", rel="self")
        fg.subtitle("Combined feed for RSS feeds")
        fg.language('en')
    except:
        log.error("Error initialising the feed!")
        sys.exit(1)

    log.debug("Feed initialised!")

    return None


def parse_rss_feed(url) -> feedparser.FeedParserDict:
    log.debug("Parsing RSS feed..")

    try:
        # Hopefully this should parse..
        return feedparser.parse(url)
    except Exception:
        log.warninging("Failed to parse RSS feed.")
        # Now, we could handle gracefully.
        # This code is a WIP, but maybe we shouldn't crash?
        log.warninging("Cannot continue, we want all the feeds to work!")
        sys.exit(1)


def main():
    log.debug("Loading feed list into memory..")
    feeds = None
    with open(FEED_LIST_PATH, "r") as infile:
        feeds = infile.read().splitlines()

    log.debug("Iterating over feed list..")
    for feed in feeds:
        FEEDS.append(feed)

    log.debug("Iterating over [input] feeds...")
    for feed in FEEDS:
        rss = parse_rss_feed(feed)
        entries = rss.get("entries")
        log.debug("Iterating over [input] feed entries..")
        for entry in entries:
            log.debug("New feed entry created.")

            fe = fg.add_entry()

            log.debug("Working on new feed entry..")

            try:
                fe.id(entry["id"])
            except:
                # Deifnitely weird...
                log.warning("Empty id attribute, defaulting..")
                fe.id("about:blank")

            try:
                fe.title(entry["title"])
            except:
                # OK, this is a definite malformed feed!
                log.warning("Empty title attribute, defaulting..")
                fe.title("Unspecified")

            try:
                fe.link(href=entry["link"])
            except:
                # When we have a empty link attribute, this isn't ideal
                # to set a default value.. :/
                log.warning("Empty link attribute, defaulting..")
                fe.link(href='about:blank')

            try:
                if entry["sources"]["authors"]:
                    for author in entry["sources"]["authors"]:
                        fe.author(author)
                elif entry["authors"]:
                    try:
                        for author in entry["authors"]:
                            fe.author(author)
                    except:
                        log.debug("Oh dear, a malformed feed! Adjusting.")
                        # This is a ugly hack to fix broken feed entries with the author attribute!
                        author["email"] = author.pop("href")
                        fe.author(author)
            except:
                # Sometimes we don't have ANY author attributes, so we
                # have to set a dummy attribute.
                log.warning("Empty authors attribute, defaulting..")
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
                log.warning(
                    "Empty description OR summary attribute, defaulting..")
                fe.description("Unspecified")
                fe.summary("Unspecified")

            try:
                if entry["published"]:
                    try:
                        fe.published(entry["published"])
                        fe.updated(entry["published"])
                    except:
                        fe.published("1970-01/01T00:00:00+00:00")
                        fe.updated("1970-01/01T00:00:00+00:00")
                        continue
            except:
                # Sometimes feeds don't even provide a publish date, so we default to
                # the start date &time of the Unix epoch.
                log.warning("Empty publish attribute, defaulting..")
                fe.published("1970-01/01T00:00:00+00:00")
                fe.updated("1970-01/01T00:00:00+00:00")


if __name__ == "__main__":
    setup_logging()
    log.debug("Initialising...")

    log.debug("Assiging variables..")
    try:
        # Configuration is specified with environemnt variables.
        log.debug("Assignment attempt: SINGLERSS_FEED_OUT_PATH")
        FEED_OUT_PATH = os.environ["SINGLERSS_FEED_OUT_PATH"]
    except KeyError:
        log.error("*** Environment variable missing! ***")
        log.error("`SINGLERSS_FEED_OUT_PATH` variable missing.")
        log.error("This program will NOT run without that set.")
        sys.exit(1)

    try:
        FEED_LIST_PATH = os.environ["SINGLERSS_FEED_LIST_PATH"]
    except:
        log.error("*** Environment variable missing! ***")
        log.error("`SINGLERSS_FEED_LIST_PATH` variable missing.")
        sys.exit(1)

    try:
        FEED_OUT_TYPE = os.environ["SINGLERSS_FEED_OUT_TYPE"]
    except KeyError:
        log.error("*** Environment variable missing! ***")
        log.error("`SINGLERSS_FEED_OUT_TYPE` variable missing.")
        log.error("This program will NOT run without that set.")
        sys.exit(1)

    log.debug("Begin initialising variables..")
    init_feed()

    log.debug("Begin processing feeds...")
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
