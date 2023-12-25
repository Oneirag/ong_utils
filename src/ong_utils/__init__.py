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

import importlib
from dataclasses import dataclass

from ong_utils.jwt_tokens import decode_jwt_token, decode_jwt_token_expiry


@dataclass
class ImportConfig:
    # path for import (e.g. ong_utils.config)
    import_string: str
    pip_install_extras: str = None


__lazy_imports = {
    'OngConfig': ImportConfig('ong_utils.config'),
    'OngTimer': ImportConfig('ong_utils.timers'),
    'create_pool_manager': ImportConfig('ong_utils.urllib3'),
    'cookies2header': ImportConfig('ong_utils.urllib3'),
    'get_cookies': ImportConfig('ong_utils.urllib3'),
    'LOCAL_TZ': ImportConfig('ong_utils.utils'),
    'is_debugging': ImportConfig('ong_utils.utils'),
    'find_available_port': ImportConfig('ong_utils.web'),
    'InternalStorage': ImportConfig('ong_utils.internal_storage'),
    'decode_jwt_token': ImportConfig('ong_utils.jwt_tokens', pip_install_extras="[jwt]"),
    'decode_jwt_token_expiry': ImportConfig('ong_utils.jwt_tokens', pip_install_extras="[jwt]"),
}

__all__ = list(__lazy_imports.keys())
# __all__ = ['OngConfig',
#            'OngTimer',
#            'create_pool_manager',
#            'cookies2header',
#            'get_cookies',
#            'LOCAL_TZ',
#            'is_debugging',
#            'find_available_port'
#            ]


def __getattr__(name):
    """Implements lazy loading"""
    if name in __all__:
        try:
            return getattr(importlib.import_module(__lazy_imports[name].import_string, __name__),
                           name)
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f"Please install dependencies with "
                                      f"'pip install ong_utils[{__lazy_imports[name].pip_install_extras}'")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

#
# from ong_utils.config import OngConfig
# from ong_utils.timers import OngTimer
# from ong_utils.urllib3 import create_pool_manager, cookies2header, get_cookies
# from ong_utils.utils import LOCAL_TZ, is_debugging
