Ong_Utils
=========

## Description
Simple package with some utils to import in any project:
* class to manage configuration files in yaml or json [Read more](#configuration-files). It also uses `keyring` to store and retrieve passwords. [Read more](#passwords)  
* logger and a timer to record elapsed times for optimizing some processes. [Read more](#timers)
* a `create_pool_manager` function to create instances of urllib3.PoolManager with retries and timeouts and checking of 
https connections. [Read more](#urllib3-utils)
* a `TZ_LOCAL` variable with the local timezone
of the computer).   
* an `is_debugging` function that returns True when debugging code
* a `to_list` function to convert any non-list value (specifically strings to avoid iterating char by char) into a list
* a `cookies2header` that converts cookies in dict to header field 'Cookie' for use in urllib3. [Read more](#urllib3-utils)
* a `get_cookies` function to extract a dict of cookies from a response of a urllib3 request. [Read more](#urllib3-utils)
* a class to store any data into keyring (e.g. strings, dicts...). [Read more](#storing-long-data-in-keyring)
* functions to parse html pages and extract javascript variables (such as CSRF tokens or links). [Read more](#parsing-html-pages)
* Class to read/apply sensitivity labels to a file (Public, Internal...) [Read more](#add-sensitivy-labels-to-office-files). It is adapated from https://github.com/brunomsantiago/mip_python
* functions to get current user and domain. [Read more](#get-current-user-and-domain)
* functions for simple input dialogs with validations using tk [Read more](#simple-dialogs)
* a function `fix_windows_gui_scale` to avoid blurry tkinter text elements in Windows 10 or 11. [Read more](#fix-windows-scaling)
* Handlers to redirect prints and logging to an Entry tkinter widget [Read more](#print-and-logging-tkinter-handlers)
### Optional dependencies
Installing `pip install ong_utils[shortcuts]`:
* functions to create desktop shortcuts for packages installed with pip. [Read more](#make-shortcuts-for-entry-points)

Installing `pip install ong_utils[xlsx]`:
* function to export a pandas dataframe into a xlsx excel sheet.[Read more](#nicer-output-pandas-dataframe-to-excel) 

Installing `pip install ong_utils[jwt]`:
* functions to decode access tokens. [Read more](#decoding-jwt-tokens)

Installing `pip install ong_utils[selenium]`:
* class to manage Chrome using selenium. [Read more](#control-webpages-with-selenium)

Installing `pip install ong_utils[office]`:
* Classes to interact with API of Office in windows. [Read more](#create-instances-of-office-programs)

Installing `pip install ong_utils[credentials]`:
* function to verify password of current log in user. [Read more](#control-webpages-with-selenium)

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
### Advanced usage
Default values can be supplied, so a new file is created with the default values if it does not exist previously
```python
from ong_utils import OngConfig
# The following code will create the config file with given default values and
# will also raise an exception to stop the program so the user can review the file
default_app_values = dict(a_kew=a_value)
cfg = OngConfig(default_app_cfg=default_app_values)

# The following code will create the config file with given default values and
# but won't raise any exception, so the process will continue
# This approach is usefull when the default values can be used without further edition
default_app_values = dict(a_kew=a_value)
cfg = OngConfig(default_app_cfg=default_app_values, 
                write_default_file=True)

```
Values could be updated and writen to the config file during the execution of the code

```python
from ong_utils import OngConfig

# Assume file already exists
cfg = OngConfig("app_name")
...
# Add a new key and saves the config file. If the key existed, raises ValueError
cfg.add_app_config("new key", "new value")
print(cfg.config("new key"))  # Will print new value
# Updates an existing key and saves in the config file. If the key did not exist, raises ValueError
cfg.update_app_config("new key", "new value")
print(cfg.config("new key"))  # Will print new value


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
# This is an optional section, for values used just in tests
my_project_test:
  sample_key1: sample_value1
  sample_key2: sample_value2

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
# Optional: test values for project_name2
project_name2_test:
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

## Parsing html pages
To extract simple values without the need for BeautifulSoup, you can use `find_js_variable`

```python
from ong_utils import find_js_variable
source = """
Imagine this is a website
var_name1="value1"
var_name2={"key1":"value2"}
"""
find_js_variable(source, 'var_name1')       # returns "value1"
find_js_variable(source, "var_name", ":")   # returns "value2"
```

## Control webpages with selenium
Install `ong_utils[selenium]` to control websites with selenium

```python
from ong_utils import Chrome

# Use it as a context manager
with Chrome(block_pages="https://www.marca.com") as chrome:
    driver = chrome.get_driver()
    driver.get("https://www.google.com")
    driver.implicitly_wait(5)
    driver.get("https://www.marca.com")
    driver.implicitly_wait(5)

# Or close driver explicitly
chrome = Chrome()
driver = chrome.get_driver()
driver.get("www.someserver.com")
chrome.quit_driver()

###############################
# Wait for a cookie in a request
###############################
driver = chrome.wait_for_cookie("someserver.com", "somecookie", timeout_headless=10, timeout=60)
if driver:
  cookies = driver.get_cookies()
  
###############################
# Wait for a certain request
###############################
req = chrome.wait_for_request("someserver.com", "someserver.com/api/interesting_endpoint", timeout_headless=10, timeout=60)
if req:
    auth = req.headers['Authorization'].split(" ")[-1]
# or the same shorter...
token = chrome.wait_for_auth_token("someserver.com", "someserver.com/api/interesting_endpoint", timeout_headless=10, timeout=60)
if token:
    do_stuff_here()
```
## Utilities for Office

### Create instances of office programs
Use classes in `ong_utils.office.office`, to open files with Offfice API in windows.

Avoids problems with cache that might happen from time to time,

Sample code:

````python
from ong_utils.office.office_base import WordBase, ExcelBase, PowerpointBase


class MyWord(WordBase):
  def __init__(self, file, logger):
    super().__init__(logger)
    self.file = self.client.Open(file)


````

### Add Sensitivy Labels to office files
Use a sample office file to apply sensitivity labels to other file, or if you know the label name, apply the label name.

Works properly with Internal and Public, might not work well with Private or Restricted files

Sample code;
````python
from ong_utils import SensitivityLabel
# Case 1: you know the sensitivity label to apply
sl = SensitivityLabel("XXXXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")
sl.apply(my_filename)
# Case 2: you don't know label name, but what to clone an existing one (must be an Excel/Word/Powerpoint file)
SensitivityLabel(reference_file).apply(my_file)
# Case 3: get label name from a file and print it
print(label_id:=SensitivityLabel(reference_file).label_id)
# label_id can be used to apply to further docs, e.g.: SensitivityLabel(label_id).apply(filename)
````

## Get current user and domain
Reads it from environ variables
```python
from ong_utils import get_current_user, get_current_domain
print(get_current_user())       # Prints current user
print(get_current_domain())     # Prints current domain. Could be empty
```

## Verify password of current log in user
Install `ong_utils[credentials]` to check correct password for current user. Works in windows and linux/macos
```python
from ong_utils import verify_credentials
username = "your current username" # get it from ong_utils.get_current_user()
domain = "your domain, needed in windows"   # For linux/macos could be empty. Get it from ong_utils.get_current_domain()
password = "your password goes here"
if verify_credentials(username, domain, password):
  print("Your password is ok")
else:
  print("Bad password")
```

## Simple dialogs
Use `ong_utils.OngFormDialog` for build a dialog with custom controls and validations.

### Custom dialog
Use `ong_utils.OngFormDialog` to build a dialog with multiple string entry items and custom validations. 
You have to add the fields with the `add_*` methods and finally call `show()` to show the form.

You can use the `set_tooltip` method to add tooltips to the fields of the form with thte given text.


Sample code to show the following window:
![dialog_form_macos.png](img%2Fdialog_form_macos.png)
```python
from ong_utils import OngFormDialog, get_current_user, get_current_domain, verify_credentials


frm = OngFormDialog(title="Sample form", description="Show descriptive message for the user")
#############
# Option 1: create the form manually, adding each field one by one
#############
frm.add_entry_field(name="domain",  # Key of the dict in the return dictionary and for validation functions
                    label="Domain",  # Name to the shown for the user
                    default_value=get_current_domain(),  # Default value to be used
                    editable=False,  # Not editable (by default all fields are editable)
                    )
frm.add_entry_field(name="username", label="User", default_value=get_current_user())
frm.add_entry_field(name="password", label="Password", default_value="").set_validation(
    # The validation function receives values of all fields, so should accept extra **kwargs
    validation_func=verify_credentials,
    # The otional validation_error_message to give an informative message to the user additional to "invalid field"
    validation_error_message="Please provide a valid user/password"
).set_show("*")  # Hide input with asterisks
frm.add_entry_field(name="server", label="Server").set_width(
    40  # Make this field wider
)

# Show the form and collect values
res = frm.show()
if res:     # if empty, user cancelled
    print(res)  # Dict with the results

#############
# Option 2: use the default functions for user, domain and password
#############
frm.clear()     # clear all fields of the form
# Add domain, user and password, chaining. User and domain are not editable by default,
# so they are made editable with the editable parameter.
# Use validate_os to False to avoid validating against system
frm.add_domain_field(editable=True).add_user_field(editable=True
                                                   ).add_password_field(validate_os=False)
# Same as above: frm.add_domain_user_password(validate_os=False)
# add the rest of the fields
frm.add_entry_field(name="server", label="Server").set_width(
    40  # Make this field wider
)
# Show the form and collect values
res = frm.show()
if res:     # if empty, user cancelled
    print(res)  # Dict with the results
```
### Additional fields (File, folder, combobox, checkbox)
The `OngFormDialog` supports other fields, such as comboboxes, checkboxes and selectors for files and folders:
```python
from ong_utils import OngFormDialog, get_current_user, get_current_domain, verify_credentials


frm = OngFormDialog(title="Sample form", description="Show descriptive message for the user")
##########
# Other fields
##########
frm.clear()
# This shows a combo box with values Yes and No, selecting Yes as default
frm.add_combo_field(name="combo", label="Select one",
                    valid_values=['Yes', "No"],
                    default_value="Yes",
                    )
# This shows an entry field to select a File, but  allows empty values (returns "")
frm.add_file_field(name="file", label="Select File", empty_ok=True)
# This shows an entry field to select a Folder, but  allows empty values (returns "")
frm.add_folder_field(name="folder", label="Select Folder", empty_ok=True)
# A checkbox that returns True/False
frm.add_boolean_field(name="bool", label="Select/Unselect", default_value=True)
# Show the form and collect values
res = frm.show()
if res:     # if empty, user cancelled
    print(res)  # Dict with the results```
```

### Login dialog form for username, domain and password
In the case of a simple login form such as
![login_form_macos.png](img%2Flogin_form_macos.png)
use the following code
```python
from ong_utils import OngFormDialog

def validation(**kwargs) -> bool:
  """A function that receives a dict and returns bool
  the dict receives the keys username, domain and password.
  Could use the ong_utils.verify_credentials to verify against current log in user
  """
  if len(kwargs['password']) > 5:
    return True
  else:
    return False

# By default, password is validated against current OS. If you want to override it,
# you need to add validate_os=False and supply your own validation function
result = OngFormDialog(title="your title goes here",
                       description="A label to show context to the user",
                       ).add_domain_user_password(
    validate_os=False).set_validation(validation, field_name="password").show()
print(result)   # could be {} if user cancelled or a dict of "username", "domain", "password"
```

## Print and logging tkinter handlers
You can use `print2widget` and `log2widget` to redirect any `print` or log to an Entry tkinter widget. See the following example:
````python
import tkinter as tk
import logging
from ong_utils import print2widget, logger2widget

class Simple:
    def __init__(self, title: str = "Simple logger"):
        self.root = tk.Tk()
        self.title = title
        
        self.root.title(self.title)

        # Central area for logs
        self.text_area = tk.Text(self.root, font=("Arial", 12))
        self.text_area.pack(fill='both', expand=True)
        # Redirects all prints from now onwards to text_area
        print2widget(self.text_area)
        self.logger = logging.getLogger(__name__)
        logger2widget(self.logger, self.text_area)
        
if __name__ == '__main__':
    app = Simple()
    app.root.mainloop()
    """Any call to print() or logger.info() will be shown in app.text_area"""
 
````

## Fix windows scaling
As answered in [https://stackoverflow.com/a/43046744](https://stackoverflow.com/a/43046744), in Windows 10 or 11, tk applications texts look blurry, such as:

![blurry_form_windows.png](img%2Fblurry_form_windows.png)

Use the function `fix_windows_gui_scale` to make it look properly like this:

![sharpened_form_windows.png](img%2Fsharpened_form_windows.png)

Some sample code (works in any OS, but will only sharpen texts in Windows):
````python
from ong_utils import fix_windows_gui_scale
fix_windows_gui_scale()
import tkinter as tk
from tkinter import ttk
# write your GUI code here...
````
