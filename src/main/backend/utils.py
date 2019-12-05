#!/usr/bin/env python3

"""
Bulk Reviewer
---
Utility module

Tim Walsh, 2019
https://bitarchivist.net
Licensed under GNU General Public License 3
https://www.gnu.org/licenses/gpl-3.0.en.html
"""
import datetime
import sys
import time


def print_to_stderr_and_exit(msg):
    """
    Print error message to stderr and exit with code 1.
    """
    msg += " See bulk-reviewer.log for details."
    print(msg, file=sys.stderr)
    sys.exit(1)


def time_to_int(str_time):
    """Convert datetime in format YYYY-MM-DDTHH:MM:SS
    to integer representing Unix time.
    """
    dt = time.mktime(datetime.strptime(str_time, "%Y-%m-%dT%H:%M:%S").timetuple())
    return int(dt)
