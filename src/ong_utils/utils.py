"""
General utils that do not need additional libraries to the ong_utils base libraries:
    - get local timezone    (uses dateutil)
    - check if is debugging
    - conversion of a value to list
    - checks if is mac, linux or windows
    - get user and domain
"""
import os
import platform
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


"""
Functions to detect under which OS the code is running
"""


def is_mac() -> bool:
    """True if running in macos"""
    return platform.system() == "Darwin"


def is_windows() -> bool:
    """True if running Windows"""
    return platform.system() == "Windows"


def is_linux() -> bool:
    """True if running Linux"""
    return platform.system() == "Linux"


"""
Functions to get current user and domain
"""


def get_current_user() -> str:
    return os.getenv("USER", os.getenv("USERNAME"))


def get_current_domain() -> str:
    return os.getenv("USERDOMAIN", "")


def get_computername() -> str:
    return platform.node()


if __name__ == '__main__':
    print(f"{get_current_user()=}")
    print(f"{get_current_domain()=}")
    print(f"{get_computername()=}")
