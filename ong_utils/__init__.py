"""
Common imports for projects
-   http: a pool manager for urllib3 that check https certificates
-   LOCAL_TZ: a timezone object with the local timezone
-   OngConfig: a config object

Reads config files from f"~/.config/ongpi/{project_name}.{extension}"
where extension can be yaml, yml, json or js
Path can be overridden either with ONG_CONFIG_PATH environ variable
"""

import certifi
import dateutil.tz
import urllib3.contrib.pyopenssl
import sys

from ong_utils.config import OngConfig
from ong_utils.timers import OngTimer

# Initialize urllib3 with SSL security enabled
urllib3.contrib.pyopenssl.inject_into_urllib3()
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                           ca_certs=certifi.where(),
                           retries=urllib3.util.Retry(
                               status=10,  # Retry 10 times on error status (e.g. after 503 error)
                               backoff_factor=0.15,  # Aprox seconds to wait between retries
                           )
                           )

LOCAL_TZ = dateutil.tz.tzlocal()


def is_debugging() -> bool:
    """Returns true if debugging"""
    gettrace = sys.gettrace()
    # Check for debugging, if so run debug server
    if gettrace:
        return True
    return False
