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


class AdditionalRequirementException(Exception):
    """Class for exceptions for lack or extras"""
    pass


def raise_extra_install(extras: str):
    """Raises exception for the user to install some extras"""

    def f(*args, **kwargs):
        raise AdditionalRequirementException(
            f"Please install extra requirements with 'pip install ong_utils[{extras}]'")

    return f


from ong_utils.config import OngConfig
from ong_utils.internal_storage import InternalStorage
from ong_utils.parse_html import find_js_variable
from ong_utils.timers import OngTimer
from ong_utils.urllib3_utils import create_pool_manager, cookies2header, get_cookies
from ong_utils.utils import LOCAL_TZ, is_debugging
from ong_utils.web import find_available_port

try:
    from ong_utils.excel import df_to_excel
except (ModuleNotFoundError, NameError):
    df_to_excel = raise_extra_install("excel")
try:
    from ong_utils.jwt_tokens import decode_jwt_token, decode_jwt_token_expiry
except (ModuleNotFoundError, NameError):
    decode_jwt_token = decode_jwt_token_expiry = raise_extra_install("jwt")
    pass
try:
    from ong_utils.selenium_chrome import Chrome
except (ModuleNotFoundError, NameError):
    Chrome = raise_extra_install("selenium")
