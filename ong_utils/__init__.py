"""
Common imports for projects
-   http: a pool manager for urllib3 that check https certificates
-   LOCAL_TZ: a timezone object with the local timezone
-   OngConfig: a config object
-   is_debugging: true if in debug code
-   get_cookies: for getting a dictionary of cookies from a urllib3 response object
-   cookies2header: transforms cookies to a dict that can be used as header parameter in urllib3 requests

Reads config files from f"~/.config/ongpi/{project_name}.{extension}"
where extension can be yaml, yml, json or js
Path can be overridden either with ONG_CONFIG_PATH environ variable
"""

import dateutil.tz
import sys


from ong_utils.config import OngConfig
from ong_utils.timers import OngTimer
from ong_utils.urlib3 import http, cookies2header, get_cookies


LOCAL_TZ = dateutil.tz.tzlocal()


def is_debugging() -> bool:
    """Returns true if debugging"""
    gettrace = sys.gettrace()
    # Check for debugging, if so run debug server
    if gettrace:
        return True
    return False
