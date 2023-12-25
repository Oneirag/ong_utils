# Ong_Utils
## Description
Simple package with some utils to import in any project:
* Class to manage configuration files in yaml or json. It also uses `keyring` to store and retrieve passwords 
* logger and a timer to record elapsed times for optimizing some processes 
* a create_pool_manager function to create instances of urllib3.PoolManager with retries and timeouts and checking of 
https connections 
* a TZ_LOCAL variable with the local timezone
of the computer).   
* a is_debugging function that returns True when debugging code
* a cookies2header that converts cookies in dict to header field 'Cookie' for use in urllib3
* a get_cookies function to extract a dict of cookies from a response of a urllib3 request
* a class to store any data into keyring (e.g. strings, dicts...)

### Optional dependencies
Installing `pip install ong_utils[shortcuts]`:
* functions to create desktop shortcuts for packages installed with pip

Installing `pip install ong_utils[xlsx]`:
* function to export a pandas dataframe into a xlsx excel sheet 

Installing `pip install ong_utils[jwt]`:
* functions to decode access tokens 

## General usage
Simple example of an __init__.py in a package ("mypackage") using ong_utils:
```python
import pandas as pd
from ong_utils import OngConfig, LOCAL_TZ, OngTimer
_cfg = OngConfig("mypackage")
config = _cfg.config
logger = _cfg.logger
```
And usage in other parts of the code of "mypackage":
```python
import pandas as pd
from mypackage import config, logger, LOCAL_TZ, http
local_now = pd.Timestamp.now(tz=LOCAL_TZ)
res = http.request("GET", config('url'))
logger.info("Sample log")
```

## Configuration files
Config files are yaml/json files located (by default) in `~/.config/ongpi/{project_name}.{extension}`. 
The file extension can be yaml, yml, json or js.
File can have this form:
```yaml
my_project:
  sample_key1: sample_value1
  sample_key2: sample_value2
log:
  optional_log_config: values
```
or this
```json
{
  "my_project": {
    "sample_key1": sample_value1,
    "sample_key2": "sample_value2"
  },
  "log": {
    "optional_log_config": value
  }
}
```
Config files must have a section with the name the project.   OngConfig.config("key") will raise an Exception if "key" is undefined, unless
a default value is used (OngConfig.config("key", "default_value"))  
If a file_path is supplied as second argument to the constructor, that file will be used. In that case many projects
can share the same config file. E.g. if config file is /etc/myconfig.yaml, ti can has this form:
```yaml
project_name1:
  key_for_project1: value
project_name2:
  key_for_project2: value
```
and config method can only access to configuration of current project.

New values can be added to the configuration in execution time by calling `add_app_config`. That will persist the new values in the configuration file.
### Passwords
Module uses keyring to store passwords
```python
from ong_utils import OngConfig
# configuration file should have "service" and "user" keys
_cfg = OngConfig("mypackage")
config = _cfg.config
get_password = _cfg.get_password
set_password = _cfg.set_password

# Sets password (prompts user)
set_password("service", "user")
# Equivalent to keyring.set_password(config("service"), config("user"), input())
# Gets password
pwd = get_password("service", "user")
# Equivalent to keyring.get_password(config("service"), config("user"))
```
## Storing long data in keyring 
### Storing json-serializable data
For storing long passwords (e.g. a jwt_token) or non string data (e.g. a dictionary of cookies), use `ong_utils.InternalStorage` class.
```python
from ong_utils import InternalStorage

internal_storage = InternalStorage("your app name")
for value to store in [
        "long string" * 120,
        {"an": "example", "of": "dictionary"}
        ]:
  key_name = "sample_key"
  internal_storage.store_value(key_name, value)
  stored = internal_storage.get_value("key name")
  assert value == stored
  internal_storage.remove_stored_value()

```
### Storing cookies from requests.session objects
`CookieJar` objects are not json serializable. To store cookies you'll have to turn into list of dicts. 

Use functions in `requests.cookies` package to make conversions before storing/retrieving them as dicts

```python
# Assume session is a request.session.Session object
cookies = session.cookies
cookie_dict = [dict(name=c.name, value=c.value, domain=c.domain, path=c.path, expires=c.expires)
               for c in cookies]
# Store cookie_dict normally

# Code for updating session from cookie_dict
import requests.cookies

# Assume cookie_dict is the same as above
cookies = [requests.cookies.create_cookie(**c) for c in cookies_dict]
for cookie in cookies:
    session.cookies.set_cookie(cookie)
```

## Timers
`OngTimer` class uses `tic(msg)` to start timer and `toc(msg)` to stop timer and show a message with the elapsed time.
Several timers can be created with different `msg`. The parameter `msg` is used to link methods `tic(msg)` and `toc(msg)`,
so the time is measured from tic to toc.Before a toc there must be a tic, so if there is not a `tic(msg)` with the same `msg` as a `toc(msg)` 
an exception is risen. 
Additionally, it can be used as a context manager

Example Usage:
```python
    from ong_utils import OngTimer
    from time import sleep

    #########################################################################################################
    # Standard use (defining an instance and using tic, toc and toc_loop methods, changing decimal places)
    #########################################################################################################
    tic = OngTimer()  # if used OngTimer(False), all prints would be disabled
    more_precise_tic = OngTimer(decimal_places=6)     # Use decimals parameter to increase decimals (defaults to 3)

    tic.tic("Starting")
    more_precise_tic.tic("Starting (6 decimals)")
    for i in range(10):
        tic.tic("Without loop")
        sleep(0.15)
        tic.toc("Without loop")
        tic.tic("Loop")
        sleep(0.1)
        if i != 5:
            tic.toc_loop("Loop")  # Will print elapsed time up to iter #5
        else:
            tic.toc("Loop")  # Will print in this case
    sleep(1)
    tic.print_loop("Loop")  # Forces print In any case it would be printed in destruction of tic instance
    tic.toc("Starting")  # Will print total time of the whole loop
    more_precise_tic.toc("Starting (6 decimals)")  # Will print total time with 6 decimals

    ########################################################################################
    # Using toc/toc_loop with a non previously defined msg will raise a ValueError Exception
    ########################################################################################
    try:
        tic.toc("This msg has not been defined in a previous tick so ValueError Exception will be risen")
    except ValueError as ve:
        print(ve)

    #############################################################
    # Use as a context manager. Won't work accumulating in a loop
    #############################################################
    with OngTimer(msg="Testing sleep"):
        print("hello context manager")
        sleep(0.27)
    with OngTimer().context_manager("Testing sleep"):  # Exactly same as above
        print("hello context manager")
        sleep(0.27)
    # Use context manager (but testing that it can be disabled)
    with OngTimer(msg="Testing sleep disabled", enabled=False):
        print("hello disabled context manager")
        sleep(0.22)
    # use global timer as context manager
    existing_instance = OngTimer()
    with existing_instance.context_manager("Example using an existing context manager instance"):
        sleep(.19)

    # Optionally: write also tick using a logger
    import logging
    logging.basicConfig(level=logging.DEBUG)
    with OngTimer(msg="Using a logger", logger=logging, log_level=logging.DEBUG):
        sleep(0.2)

    ##############################################################
    # When a timer is deleted, any tic without toc will be printed
    ##############################################################
    forgoten_toc_timer = OngTimer()             # This timer will have tics without corresponding toc
    standard_timer = OngTimer(decimals=6)
    forgoten_toc_timer_disabled = OngTimer(enabled=False)
    forgoten_toc_timer.tic("forgotten timer1")
    forgoten_toc_timer.tic("forgotten timer2")
    standard_timer.tic("unforgotten timer")
    forgoten_toc_timer_disabled.tic("forgotten disabled timer")
    sleep(0.1)
    standard_timer.toc("unforgotten timer")
    del forgoten_toc_timer   # Will print elapsed time, as are pending tocs
    del standard_timer   # Prints nothing (as there is not pending tic)
    del forgoten_toc_timer_disabled     # Prints nothing (is disabled)

    #####################################################
    # Use .msgs property to iterate over all named timers
    #####################################################
    loop_timer = OngTimer()
    for _ in range(10):
        loop_timer.tic("hello1")
        loop_timer.tic("hello2")
        sleep(0.1)
        loop_timer.toc_loop("hello1")
        loop_timer.toc_loop("hello2")
    for msg in loop_timer.msgs:
        loop_timer.print_loop(msg)

```
## Urllib3 utils
Module ong_utils.urllib3 includes simple functions to treat cookies in urllib3.

Example:
```python
from ong_utils import create_pool_manager, cookies2header, get_cookies
url = "whichevervalidurl"
http = create_pool_manager()    # Creates a PoolManager with retries
req = http.request("get", url)
# get cookies (as a dict)
cookies = get_cookies(req)
headers = {"Accept": "text/html;application/json"}
# append cookies to the headers dict
headers.update(cookies2header(cookies))
req.http.request("get", url, headers=headers)       # Using cookies from previous response
```

## Make shortcuts for entry points

You can create desktop shortcuts for each entry point in the script to easily launch them in your system.

You have to install optional dependency `pip install ong_utils[shortcuts]`

**NOTE**: for the shortcut to work, each entry point defined in e.g. `script_file` of package `package` must be
executable with `python -m package.script_file`

There are two ways to create shortcuts:

* **Create shortcuts when installing with pip:** valid when installing from git (e.g. pip install
  git+https://github.com/someone/somerepo.git). Uses a custom postinstall
  script that creates the desktop launcher and modifies the wheel file (so they can be uninstalled) after building the
  wheel file from sources.
* **Create a script and run it manually after install:** valid for any other case. Create a entry_point
  e.g. `post_install` and call it manually after installation. That scritp will create the shortcut(s) and add it/them
  to
  the `RECORD`file so the shortcut will be later uninstalled

### Create the shortcut when installing with PIP

Create a `setup.py` in your root directory and add the following code:

```python
from setuptools import setup
from ong_utils.desktop_shortcut import PipCreateShortcut

setup(cmdclass={'bdist_wheel': PipCreateShortcut})

```

In your `pyproject.toml` add the following:

```toml
[build-system]
requires = [
    "setuptools",
    "wheel",
    "ong_utils[shortcuts]"
]
[project.scripts]
script1 = "package.file:function"
```

Then the program will install the wheel from pip and create a desktop shortcut for script1.

### Create a manual script

Provided that you have the following entry point in your `pyproject.toml`:

```toml
[project.scripts]
script1 = "mypackage.myscript:myfunction"
```

You'll have to create a script in your code. Let's call it `post_install.py` with the following content:

```python
from ong_utils.desktop_shortcut import PostInstallCreateShortcut


def main():
    PostInstallCreateShortcut("your_library_name").make_shortcuts()


if __name__ == '__main__':
    main()
```

Assuming that `post_install.py` script is in the `mypackage` folder, then you have to ask the user to run it manually
after installation:

```bash
pip install mypackage
python -m mypackage.post_install
```

**NOTE**: optionally, you can add icons to the shorcut with png format or icns
format (for mac), provided that the icons have the same name as the entry_point. The program will use the first icon
that matches the name of the entry point.

## Nicer output pandas DataFrame to Excel
You can export a pandas DataFrame to Excel nicely formated (converted to an Excel Table, with autofilter enabled and columns widths autofitted)

Example:
```python
import pandas as pd
from ong_utils import df_to_excel

with pd.ExcelWriter(filename) as writer:
    df_to_excel(df, writer, sheet_name)
```

## Decoding jwt tokens
Needs install extra packages with `pip install ong_utils[jwt]`

Use `ong_utils.decode_jwt_token` to decode a jwt token into a dict. 

Use `ong_utils.decode_jwt_token_expiry` to decode expiration as a datetime object. 

