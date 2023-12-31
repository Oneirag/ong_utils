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


def to_list(value) -> list:
    """
    Converts a value to a list
    :param value: a value that is not a list (or tuple)
    :return: value converted into a list or tuple
    """
    if isinstance(value, (list, tuple)):
        return value
    return [value]
