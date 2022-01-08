"""
Common imports for projects
-   create_pool_manager: to create a pool manager for urllib3 that check https certificates
-   LOCAL_TZ: a timezone object with the local timezone
-   OngConfig: a config object
-   is_debugging: true if in debug code
-   get_cookies: for getting a dictionary of cookies from a urllib3 response object
-   cookies2header: transforms cookies to a dict that can be used as header parameter in urllib3 requests

Reads config files from f"~/.config/ongpi/{project_name}.{extension}"
where extension can be yaml, yml, json or js
Path can be overridden either with ONG_CONFIG_PATH environ variable
"""


from ong_utils.config import OngConfig
from ong_utils.timers import OngTimer
from ong_utils.urllib3 import create_pool_manager, cookies2header, get_cookies
from ong_utils.utils import LOCAL_TZ, is_debugging

