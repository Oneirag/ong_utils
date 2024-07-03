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
from ong_utils.import_utils import AdditionalRequirementException, raise_extra_install

from ong_utils.config import OngConfig
from ong_utils.internal_storage import InternalStorage
from ong_utils.parse_html import find_js_variable
from ong_utils.timers import OngTimer
from ong_utils.urllib3_utils import create_pool_manager, cookies2header, get_cookies
from ong_utils.utils import (LOCAL_TZ, is_debugging, to_list, is_mac, is_linux, is_windows, get_current_user,
                             get_current_domain)
from ong_utils.web import find_available_port
from ong_utils.ui import simple_dialog, user_domain_password_dialog, fix_windows_gui_scale, OngFormDialog
from ong_utils.ui_logging_utils import print2widget, logger2widget
from ong_utils.async_utils import asyncio_run


import_excepts = (ModuleNotFoundError, NameError, AdditionalRequirementException)
try:
    from ong_utils.excel import df_to_excel
    from ong_utils.sensitivity_labels import SensitivityLabel
except import_excepts:
    df_to_excel = raise_extra_install("xlsx")
try:
    from ong_utils.jwt_tokens import decode_jwt_token, decode_jwt_token_expiry
except import_excepts:
    decode_jwt_token = decode_jwt_token_expiry = raise_extra_install("jwt")
    pass
try:
    from ong_utils.selenium_chrome import Chrome
except import_excepts:
    Chrome = raise_extra_install("selenium")
try:
    from ong_utils.credentials import verify_credentials
except import_excepts:
    verify_credentials = raise_extra_install("credentials")

