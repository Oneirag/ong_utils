# Ong_Utils
Simple package with some utils to import in any project:
* Class to manage configuration files in yaml or json 
* logger and a timer to record elapsed times for optimizing some processes 
* a http instance of urllib3 with retries and timeouts 
* a TZ_LOCAL variable with the local timezone
of the computer).   
* a is_debugging function that returns True when debugging code
* a cookies2header that converts cookies in dict to header field 'Cookie' for use in urllib3
* a get_cookies function to extract a dict of cookies from a response of a urllib3 request


Simple example of an __init__.py in a package ("mypackage") using ong_utils:
```python
import pandas as pd
from ong_utils import OngConfig, LOCAL_TZ, http, OngTimer
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
and config method can only access to configuration of current project
## Timers
`OngTimer` class uses `tic(msg)` to start timer and `toc(msg)` to stop timer and show a message with the elapsed time.
Several timers can be created with different `msg`. The parameter `msg` is used to link methods `tic(msg)` and `toc(msg)`,
so the time is measured from tic to toc.Before a toc there must be a tic, so if there is not a `tic(msg)` with the same `msg` as a `toc(msg)` 
an exception is risen. Example Usage:
```python
    from ong_utils import OngTimer
    from time import sleep

    tic = OngTimer()    # if used OngTimer(False), all prints would be disabled

    tic.tic("Starting")
    for i in range(10):
        tic.tic("Without loop")
        sleep(0.15)
        tic.toc("Without loop")
        tic.tic("Loop")
        sleep(0.1)
        if i != 5:
            tic.toc_loop("Loop")        # Will print elapsed time up to iter #5
        else:
            tic.toc("Loop")             # Will print in this case
    sleep(1)
    tic.print_loop("Loop")           # Forces print In any case it would be printed in destruction of tic instance
    tic.toc("Starting")     # Will print total time of the whole loop
    tic.toc("This msg has not been defined in a previous tick so exception will be risen")
```
