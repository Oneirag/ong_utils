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


# Initialize urllib3 with SSL security enabled
urllib3.contrib.pyopenssl.inject_into_urllib3()
http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                           ca_certs=certifi.where(),
                           retries=urllib3.util.Retry(
                               status=10,  # Retry 10 times on error status (e.g. after 503 error)
                               backoff_factor=0.15,  # Aprox seconds to wait between retries
                           )
                           )


def cookies2header(cookies: dict) -> dict:
    """Converts cookies in dict to header field 'Cookie' for use in urllib3"""
    return dict(Cookie="; ".join(f"{k}={v}" for k, v in cookies.items()))


def get_cookies(resp) -> dict:
    """Gets cookies from response of an urllib3 function (request, urlopen)"""
    cj = CookieJar()
    cks = cj.make_cookies(resp, Request(resp.geturl()))
    cookies = {c.name: c.value for c in cks}
    return cookies
