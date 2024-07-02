"""
Controls Chrome web browser
Needs to download webdriver for Chrome from https://sites.google.com/chromium.org/driver/
"""
from __future__ import annotations

import logging

from ong_utils.import_utils import raise_extra_exception
from ong_utils.utils import is_mac
try:
    import selenium.common.exceptions
    from selenium import webdriver as selenium_webdriver
    from seleniumwire import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait
    import seleniumwire.undetected_chromedriver as uc
except ModuleNotFoundError:
    raise_extra_exception("selenium")


class Chrome:

    def __init__(self, driver_path: str = None, profile_path: str = None, undetected: bool = False,
                 logger: logging.Logger = None, block_pages: str | list = None, use_selenium: bool = False):
        """
        Initializes a selenium Chrome web driver using seleniumwire
        :param driver_path: path for Chrome web driver executable (defaults to current path)
        :param profile_path: path for Chrome profile (navigate to chrome://settings). If None,
        :param undetected: True to use undetected chrome driver under seleniumwire
        :param logger: optional logger for informing about building driver
        :param block_pages: a page (or list of pages) to intercept block
        :param use_selenium: True to use standard selenium driver, False (default) to use seleniumwire
        """
        self.logger = logger
        self.undetected = undetected
        self.use_selenium = use_selenium
        if self.use_selenium and self.undetected:
            raise ValueError("You cannot use use_selenium=True and undetected=True at the same time")
        self.driver_path = driver_path
        self.profile_path = profile_path
        self.__driver = None
        if isinstance(block_pages, str):
            self.__block_pages = [block_pages]
        elif isinstance(block_pages, (list, tuple)):
            self.__block_pages = block_pages
        else:
            self.__block_pages = list()

    def interceptor(self, request):
        """Blocks access to self.__block_pages"""
        if not self.__block_pages:
            return
        elif any(request.url.startswith(blocked) for blocked in self.__block_pages):
            request.abort()

    def get_driver(self, headless: bool = False, reuse_last: bool = False, seleniumwire_options: dict = None):
        """
        Starts chrome and returns driver instance
        :param headless: True to run in headless mode. Defaults to False
        :param reuse_last: True to return last opened driver (if any), False (default) to create a new one
        :param seleniumwire_options: optional dict to pass to seleniumwire
        :return: a chrome driver
        """
        seleniumwire_options = seleniumwire_options or dict()
        if reuse_last and self.__driver is not None:
            return self.__driver
        self.quit_driver()     # Close previous driver instances
        if self.undetected:
            options = uc.ChromeOptions()
        else:
            options = webdriver.ChromeOptions()
        # Avoid annoying messages on chrome startup
        options.add_argument("--disable-notifications")
        options.add_argument("google-base-url=about:blank")
        if self.driver_path:
            options.binary_location = self.driver_path
        if self.profile_path:
            options.add_argument(f"user-data-dir={self.profile_path}")
        if headless:
            options.add_argument("--headless=new")  # for Chrome >= 109
        if self.logger:
            self.logger.debug(f"Initializing driver with options: {options}")
        try:
            if self.undetected:
                self.__driver = uc.Chrome(options=options, seleniumwire_options=seleniumwire_options)
            elif not self.use_selenium:
                self.__driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
            else:
                self.__driver = selenium_webdriver.Chrome(options=options)
        except selenium.common.exceptions.SessionNotCreatedException as snce:
            if is_mac():   # is macos
                cmd = r"sudo killall Google\ Chrome"
                print(f"Could not create session. Try executing '{cmd}'")
            raise
        except selenium.common.exceptions.NoSuchDriverException as nsde:
            error_msg = "Chrome not found. Download driver from 'https://chromedriver.chromium.org/downloads'"
            if self.logger:
                self.logger.error(error_msg)
            else:
                print(error_msg)
            raise
        if self.__block_pages:
            self.__driver.request_interceptor = self.interceptor
        return self.__driver

    def __iterate__driver(self, url: str, timeout: int, timeout_headless: int):
        """Opens an url twice, first headless and later interactive. If url is empty does not open it and reuses
        current driver"""
        for to, headless in (timeout_headless, True), (timeout, False):
            if to:
                if self.logger:
                    self.logger.debug(f"Opening {headless=} {url=}")
                if url:
                    self.get_driver(headless=headless).get(url)
                yield to

    def wait_for_cookie(self, url: str, cookie_name: str | list, timeout: int, timeout_headless: int = 0):
        """
        Opens and url and waits for a certain cookie. Returns driver if cookie found or None otherwise
        Attempts twice: first headless (if timeout_headless is greater than 0) and then interactive
        :param url: url to open
        :param cookie_name: cookie name (or list of cookies) for waiting for. If it is a list, stops when one of
        them is detected
        :param timeout_headless: seconds to wait for cookie in headless mode
        :param timeout: seconds to wait for cookie
        :return: driver instance or None if could not get cookie
        """
        if isinstance(cookie_name, str):
            cookie_name = [cookie_name]
        for to in self.__iterate__driver(url, timeout_headless=timeout_headless, timeout=timeout):
            try:
                WebDriverWait(self.__driver, timeout=to).until(lambda d: any(d.get_cookie(c) for c in cookie_name))
                if self.logger:
                    self.logger.info(f"Cookie {cookie_name} found in {url}")
                return self.__driver
            except TimeoutException:
                pass
        return None

    def wait_for_auth_token(self, url: str | None, request_url: str, timeout: int, timeout_headless: int = 0) \
            -> str | None:
        """
        Opens and url and waits for a request to a certain url, returning auth header token (returns XXX in a header
        Authorization: Bearer XXX) and None if not found
        Attempts twice: first headless (if timeout_headless is greater than 0) and then interactive
        :param url: url to open. If None, current driver is used (so no headless option is available)
        :param request_url: request url waiting for
        :param timeout_headless: seconds to wait for cookie in headless mode
        :param timeout: seconds to wait for cookie
        :return: authorization token or None
        """
        req = self.wait_for_request(url, request_url, timeout, timeout_headless)
        if req is not None:
            token = req.headers['Authorization'].split(" ")[-1]
            return token
        return None

    def wait_for_request(self, url: str | None, request_url: str, timeout: int, timeout_headless: int = 0):
        """
        Opens and url and waits for a request to a certain url. Returns request if found or None otherwise
        Attempts twice: first headless (if timeout_headless is greater than 0) and then interactive
        :param url: url to open. If None, current driver is used (so no headless option is available)
        :param request_url: request url waiting for
        :param timeout_headless: seconds to wait for cookie in headless mode
        :param timeout: seconds to wait for cookie
        :return: driver instance or None if program could not get cookie
        """
        for to in self.__iterate__driver(url, timeout_headless=timeout_headless, timeout=timeout):
            try:
                req = self.__driver.wait_for_request(request_url, timeout=to)
                if self.logger:
                    self.logger.info(f"Request to {request_url} found in {url}")
                return req
            except TimeoutException:
                pass
        return None

    def quit_driver(self):
        """Quits driver instance"""
        if self.__driver is not None:
            if self.logger:
                self.logger.debug("Quitting driver")
            self.__driver.quit()
            self.__driver = None

    def close_driver(self):
        """Closes driver instance"""
        if self.__driver is not None:
            self.__driver.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit_driver()


if __name__ == '__main__':
    from ong_utils import Chrome
    with Chrome(block_pages="https://www.marca.com") as chrome:
        driver = chrome.get_driver()
        driver.get("https://www.google.com")
        driver.implicitly_wait(5)
        driver.get("https://www.marca.com")
        driver.implicitly_wait(5)

