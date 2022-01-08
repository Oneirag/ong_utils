"""
Utility functions related to urllib3 package

examples:
from ong_utils import http, cookies2header, get_cookies
url = "whicheverurl"
req = http.request("get", url)
cookies = get_cookies(req)
headers = {"Accept": "text/html;application/json"}
headers.update(cookies2header(cookies))
req.http.request("get", url, headers=headers)       # Using cookies from previous response
"""

import certifi
import urllib3.contrib.pyopenssl
from http.cookiejar import CookieJar
from urllib.request import Request


def create_pool_manager(status=10, backoff_factor=0.15) -> urllib3.PoolManager:
    """
    Creates an urllib3.PoolManager instance, that checks https connections and optionally retries queries
    :param status: param to urllib3.util.Retry. Means number of times to retry in case of an error status
    (e.g. after 503 error), by default 10. Use 0 or None to disable retries
    :param backoff_factor: param to urllib3.util.Retry. Means, more or less, seconds to wait between retries
    (read urllib3.util.Retry docs for more details)
    :return: a urllib3.PoolManager that can be use with .request or .openurl methods
    """
    urllib3.contrib.pyopenssl.inject_into_urllib3()
    if status is not None and status > 0:
        retries = urllib3.util.Retry(
            status=status,      # Retry 10 times on error status (e.g. after 503 error)
            backoff_factor=backoff_factor,      # Aprox seconds to wait between retries
        )
    else:
        retries = None
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                               ca_certs=certifi.where(),
                               retries=retries
                               )
    return http

    pass


def cookies2header(cookies: dict) -> dict:
    """Converts cookies in dict to header field 'Cookie' for use in urllib3"""
    return dict(Cookie="; ".join(f"{k}={v}" for k, v in cookies.items()))


def get_cookies(resp) -> dict:
    """Gets cookies from response of an urllib3 function (request, urlopen)"""
    cj = CookieJar()
    cks = cj.make_cookies(resp, Request(resp.geturl()))
    cookies = {c.name: c.value for c in cks}
    return cookies
