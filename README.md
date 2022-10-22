# Ong_Utils
Simple package with some utils to import in any project:
* Class to manage configuration files in yaml or json. It also uses `keyring` to store and retrieve passwords 
* logger and a timer to record elapsed times for optimizing some processes 
* a create_pool_manager function to create instances of urllib3.PoolManager with retries and timeouts and checking of 
https connections 
* a TZ_LOCAL variable with the local timezone
of the computer).   
* an `is_debugging` function that returns True when debugging code
* a `cookies2header` that converts cookies in dict to header field 'Cookie' for use in urllib3
* a `get_cookies` function to extract a dict of cookies from a response of a urllib3 request
* a `find_available_port` function to find the first available port for running a flask server (incrementing by one from a 
given one until a free is found)


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
