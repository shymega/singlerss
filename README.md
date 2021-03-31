singlerss
=========

# Description

singlerss combines all feeds described in a OPML file into one feed. This can
either be outputted into `stdout` or a file, as specifed by program arguments,
and configured by the environment variables.

# Configuration

SingleRSS is configured by environment variables.

See `.env.sample`. You _must_ copy `.env.sample` to `.env` if using Docker.

`SINGLERSS_FEED_OUT_PATH` defines the relative OR absolute path to output the
feed to, _IF_ `SINGLERSS_FEED_OUT_TYPE` is set to `file`. If
`SINGLERSS_FEED_OUT_TYPE` is set to `stdout`, you must redirect output to the
file you want it written to.

`SINGLERSS_FEED_LIST_PATH` must be set to the input list of feeds you want to be
collated into one feed. This _must_ be a newline delimited file of URLs.

## Running

You may run this directly, after sourcing `.env` and exporting the variables,
with `./singlerss.py`. Alternatively, I have provided a systemd unit and timer,
which I will offer support for, and a basic crontab. I do not use cron, so I
cannot offer support for it.

# Licensing

This program is [licensed][license] under the Apache License 2.0.

Copyright (c) Dom Rodriguez (shymega) 2020.
Modified by Dag Calafell, III

[license]: /LICENSE
