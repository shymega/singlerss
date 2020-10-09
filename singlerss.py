#!/usr/bin/env python3

# Copyright (c) Dom Rodriguez 2020
# Licensed under the Apache License 2.0

import os
import sys
import feedparser
import logging
import listparser
import argparse
from os import environ
from feedgen.feed import FeedGenerator
import json

log = None
fg = None
FEED_OUT_PATH = None
FEED_OUT_TYPE = None
FEED_LIST_PATH = None
FEEDS = []
CFG = None



def setup_logging() -> None:
    """
    This function intiialises the logger framework.
    """
    global log

    LOG_LEVEL = environ.get("SR_LOG_LEVEl", "ERROR")
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
    log.debug("Initialising the feed...")

    global fg

    try:
        fg = FeedGenerator()
        # Setup [root] feed attributes
        fg.id("https://www.dagzure.com/dynamics_feed.xml")
        fg.title("Dynamics 365 Feeds")
        fg.generator("SingleRSS/v1.0.1")
        fg.link(href="https://www.dagzure.com/dynamics_feed.xml", rel="self")
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
        log.warning("Failed to parse RSS feed: " + url)


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
        log.debug("  " + feed)
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
    default_FEED_OUT_PATH = None
    default_FEED_LIST_PATH = ''
    default_FEED_OUT_TYPE = None

    try:
        default_FEED_OUT_PATH = os.environ["SINGLERSS_FEED_OUT_PATH"]
    except KeyError:
        log.debug("`SINGLERSS_FEED_OUT_PATH` environment variable missing.")

    try:
        default_FEED_LIST_PATH = os.environ["SINGLERSS_FEED_LIST_PATH"]
    except KeyError:
        log.debug("`SINGLERSS_FEED_LIST_PATH` environment variable missing.")

    try:
        default_FEED_OUT_TYPE = os.environ["SINGLERSS_FEED_OUT_TYPE"]
    except KeyError:
        log.debug("`SINGLERSS_FEED_OUT_TYPE` environment variable missing.")

    parser = argparse.ArgumentParser(description='Consolidate RSS feeds.',epilog='All arguments can be specified in the command line or the environment variables.')
    parser.add_argument('feed_list_path', type=str, help="The path to the OPML file containing the list of feeds to consolidate.", default=default_FEED_LIST_PATH)
    parser.add_argument('feed_out_type', choices=['file', 'stdout'], help="How should the output be directed?  stdout or file", default=default_FEED_OUT_TYPE)
    parser.add_argument('feed_out_path', type=str, help="The path to save the consolidated RSS file when the output type is 'file'.", default=default_FEED_OUT_PATH)
    args = parser.parse_args()

    FEED_OUT_PATH = args.feed_out_path
    FEED_LIST_PATH = args.feed_list_path
    FEED_OUT_TYPE = args.feed_out_type

    log.debug("Begin initialising variables...")
    init_feed()

    log.debug("Begin processing feeds...")
    main()

    if FEED_OUT_TYPE == "stdout":
        log.debug("stdout output specified, outputting to stdout.")
        print(fg.rss_str().decode('utf-8'))
    elif FEED_OUT_TYPE == "file":
        log.debug("File output specified, outputting to specified file...")
        fg.rss_file(FEED_OUT_PATH)
    else:
        log.error("Unknown type of output preference, cannot run.")
        sys.exit(1)
