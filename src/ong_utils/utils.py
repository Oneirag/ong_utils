import sys

import dateutil.tz

LOCAL_TZ = dateutil.tz.tzlocal()


def is_debugging() -> bool:
    """Returns true if debugging"""
    gettrace = sys.gettrace()
    # Check for debugging, if so run debug server
    if gettrace:
        return True
    return False
