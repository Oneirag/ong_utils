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

from http.cookiejar import CookieJar
from urllib.request import Request
from urllib3.response import HTTPResponse

import certifi
import urllib3.contrib.pyopenssl


def create_pool_manager(status=10, backoff_factor=0.15, **kwargs) -> urllib3.PoolManager:
    """
    Creates an urllib3.PoolManager instance, that checks https connections and optionally retries queries
    :param status: param to urllib3.util.Retry. Means number of times to retry in case of an error status
    (e.g. after 503 error), by default 10. Use 0 or None to disable retries
    :param backoff_factor: param to urllib3.util.Retry. Means, more or less, seconds to wait between retries
    (read urllib3.util.Retry docs for more details), by default 0.15
    :param kwargs: any other parameter will be passed to urllib3.util.Retry
    :return: an urllib3.PoolManager instance that can be use with .request or .openurl methods
    """
    urllib3.contrib.pyopenssl.inject_into_urllib3()
    if status is not None and status > 0:
        retries = urllib3.util.Retry(
            status=status,      # Retry 10 times on error status (e.g. after 503 error)
            backoff_factor=backoff_factor,      # Aprox seconds to wait between retries
            **kwargs
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


def get_cookies(resp: HTTPResponse, request: Request = None) -> dict:
    """Gets cookies from response of an urllib3 function (request, urlopen)"""
    cj = CookieJar()
    if request is None:
        try:
            url = resp.geturl()
            request = request or Request(url)
        except ValueError:
            # Not a valid url, fix it getting host address from pool (if any)
            if pool := getattr(resp, "_pool"):
                request = Request(f"{pool.scheme}://{pool.host}:{pool.port}{resp.geturl()}")
            else:
                raise
    cks = cj.make_cookies(resp, request)
    cookies = {c.name: c.value for c in cks}
    return cookies
