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


def print_to_stderr_and_exit(msg):
    """
    Print error message to stderr and exit with code 1.
    """
    msg += " See bulk-reviewer.log for details."
    print(msg, file=sys.stderr)
    sys.exit(1)