"""
Functions to find simple elements in websites, without the need for BeautifulSoup
"""
from __future__ import annotations

import re


def find_js_variable(page_source: str, variable_name: str, sep="=") -> str | None:
    """
    Extracts value for a js variable or dictionary
    Examples:
    find_js_variable(source, 'var_name') returns some_value if content has var_name="some_value"
    find_js_variable(source, "var_name", ":") returns some_value if content has
    "var_name":"some_value"
    :param page_source: text of the page, such as response.content from requests
    :param variable_name: name of the variable to look for
    :param sep: separator between key and value, can be either "=" (default) or ":"
    :return: The first found value or None if no value was found
    """
    pattern = fr'[\"|\']?{variable_name}[\"|\']?\s?{sep}\s?[\"|\'](?P<value>.*?)[\"|\']'
    found = re.findall(pattern, page_source)
    if found:
        return found[0]
    return None


