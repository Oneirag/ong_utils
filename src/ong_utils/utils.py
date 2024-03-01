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


class _BoolVariableFunction:
    """Create an instance of this class with a boolean value and assign it to a variable.
    The variable will evaluate to the given boolean, and so will do a functon call to the variable
    Example: will print "False" in both cases
        a = _BoolVariableFunction(False)
        if a:
            print("True")
        else:
            print("False")
        if a():
            print("True")
        else:
            print("False")
    """

    def __init__(self, value: bool):
        self.value = value

    def __bool__(self):
        """To evaluate as a variable"""
        return self.value

    def __call__(self, *args, **kwargs):
        """To evaluate as a function"""
        return self.value

    def __eq__(self, other):
        """For comparisons"""
        return self.value == other


# Check for debugging, if so run debug server
is_debugging = _BoolVariableFunction(True if sys.gettrace() else False)


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


class _PlatformVariableFunction(_BoolVariableFunction):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        super().__init__(platform.system() == self.platform_name)


"""True if running in macos"""
is_mac = _PlatformVariableFunction("Darwin")

"""True if running Windows"""
is_windows = _PlatformVariableFunction("Windows")

"""True if running Linux"""
is_linux = _PlatformVariableFunction("Linux")

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
