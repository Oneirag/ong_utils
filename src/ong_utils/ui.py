"""
Simple ui screens
"""
from __future__ import annotations

import abc
import gettext
import locale
import os.path
from dataclasses import dataclass
from tkinter import filedialog
from tkinter import ttk, messagebox, END
from tkinter.simpledialog import Dialog
from typing import List, Callable
from functools import partial

from ong_utils import is_windows
# from ong_utils.credentials import verify_credentials
from ong_utils.utils import get_current_user, get_current_domain


def fix_windows_gui_scale():
    """Fixes "strange" look of tk in windows due to bad scaling,
    based on https://stackoverflow.com/a/43046744"""
    if is_windows():
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)


fix_windows_gui_scale()

# Configure localization
locale.setlocale(locale.LC_ALL, "")  # Use the system's default locale
lang = locale.getlocale()[0]
translation = gettext.translation("messages", localedir="locales", languages=[lang], fallback=True)
translation.install()

# Define _() as the translation function
_ = translation.gettext

_STATE_ENABLED = "normal"
_STATE_DISABLED = "disabled"  # 'readonly' could also work


class _UiBaseButton:
    @abc.abstractmethod
    def button_name(self) -> str | None:
        return None

    @abc.abstractmethod
    def button_command(self, entry: ttk.Entry):
        """What to do when button is pressed. Receives an entry which is the one that has the attached info"""
        pass

    def make_button(self, master, entry: ttk.Entry) -> ttk.Button:
        return ttk.Button(master, text=self.button_name(), command=self.button_command(entry=entry))

    @abc.abstractmethod
    def validate(self, value: str) -> bool:
        """Validates the button"""
        return True


class UiFolderButton(_UiBaseButton):
    def button_name(self) -> str | None:
        return "..."

    def button_command(self, entry: ttk.Entry):
        folder_selected = filedialog.askdirectory(initialdir=entry.get(), title="Selecciona una carpeta")
        if folder_selected:
            entry.delete(0, END)
            entry.insert(0, folder_selected)

    def validate(self, value: str) -> bool:
        return os.path.isdir(value)


class UiFileButton(_UiBaseButton):
    def button_name(self) -> str | None:
        return "..."

    def button_command(self, entry: ttk.Entry):
        file_selected = filedialog.askopenfilename(initialdir=entry.get(), title="Selecciona un fichero")
        if file_selected:
            entry.delete(0, END)
            entry.insert(0, file_selected)

    def validate(self, value: str) -> bool:
        return os.path.isfile(value)


class UiPasswordButton(_UiBaseButton):
    view = True
    show = None

    def button_name(self) -> str | None:
        return "Ver"

    def button_command(self, entry: ttk.Entry):
        if self.view:
            self.show = entry.cget("show")
            entry.configure(show="")
        else:
            entry.configure(show=self.show)
        self.view = not self.view

    def validate(self, value: str) -> bool:
        return True


@dataclass
class UiField:
    name: str  # Name of the field (for internal code)
    label: str  # Label of the field (that will be shown in the window and translated)
    default_value: str = ""  # Default value
    show: str = None  # For passwords use "*"
    # Validation function, that will receive all field names of the window, so need **kwargs
    validation_func: Callable[[dict], bool] = None
    # state of the tk.Entry. True is editable, false will make not editable
    editable: bool = True
    # Width parameter of an Entry field, make it longer if needed
    width: int = 20
    # Include an additional Button
    button: _UiBaseButton = None

    @property
    def state(self):
        """Turns editable into the string state parameter of the tk.Entry"""
        return _STATE_ENABLED if self.editable else _STATE_DISABLED


class _UiFieldButton(UiField):
    @abc.abstractmethod
    def button_command(self, entry: ttk.Entry):
        print("Executing parent command")
        pass

    @abc.abstractmethod
    def button_name(self) -> str:
        pass


class _SimpleDialog(Dialog):
    def __init__(self, title: str, description: str, field_list: List[UiField], parent=None):
        self.description = description
        self.field_list = field_list
        self.__values = dict()
        self.ui_fields = dict()
        self.validated = False
        Dialog.__init__(self, parent, title)

    def body(self, master):
        """Creates ui elements for the body, returns the one that will take focus"""
        description_label = ttk.Label(master, text=self.description)
        description_label.grid(row=0, column=0, pady=5, padx=10, columnspan=2)
        focus = description_label
        for row, field in enumerate(self.field_list):
            # Label and entry for the username
            label = ttk.Label(master, text=_(field.label))
            label.grid(row=row + 1, column=0, pady=5, padx=10, sticky="w")
            entry = ttk.Entry(master, show=field.show, width=field.width)
            entry.insert(0, field.default_value)
            if not field.editable:
                # entry.configure(state='readonly')
                entry.configure(state=_STATE_DISABLED)
            entry.grid(row=row + 1, column=1, pady=5, padx=(10, 10), sticky="w")
            if field.button:
                btn = ttk.Button(master, text=field.button.button_name(),
                                 command=partial(field.button.button_command, entry=entry))
                btn.grid(row=row + 1, column=1, pady=5, padx=(0, 10), sticky="e")
            self.ui_fields[field.name] = entry
            focus = entry
        return focus

    def validate(self):
        """Validates form, returning 1 if ok and 0 otherwise. Shows error messages if it does not work"""
        try:
            self.update_values()
            for field in self.field_list:
                if ((field.validation_func and not field.validation_func(**self.__values)) or
                        field.button and not field.button.validate(self.__values[field.name])):
                    messagebox.showerror(_("Error"), _("Invalid field") + ": " + _(field.label))
                    return 0
            self.validated = True
            return 1
        except Exception as e:
            print(e)
            return 0

    def update_values(self):
        for field in self.field_list:
            self.__values[field.name] = self.ui_fields.get(field.name).get() if field.name in self.ui_fields else None

    @property
    def return_values(self) -> dict:
        """Returns a dict of field names and values, or an empty dict if validation failed"""
        if self.validated:
            return self.__values
        else:
            return dict()


def simple_dialog(title: str, description: str, field_list: List[UiField], parent=None) -> dict:
    """Shows a dialog with the given title, and description and fields and returns a dict with
    the values.
    Example:
        from ong_utils.credentials import verify_credentials
        field_list = [UiField(name="domain", label="Domain", default_value="homecomputer"),
                  UiField(name="username", label="User", default_value="homeuser"),
                  UiField(name="password", label="Password", default_value="",
                          show="*",
                          validation_func=verify_credentials),
                  UiField(name="server", label="Servidor")]
        result = dialog(title, description, field_list)
    """
    win = _SimpleDialog(title, description, field_list, parent=parent)
    return win.return_values


def user_domain_password_dialog(title: str, description: str, validate_password: Callable[[dict], bool] = None,
                                parent=None, default_values: dict = None) -> dict:
    """
    A dialog windows that asks for username, domain and password, and optionally validates it.
    :param title: title of the dialog window
    :param description: a label that will be shown before the entry fields to show help for the user
    :param validate_password: an optional function that will receive "username", "domain" and "password" named args
    and returns bool. You can use ong_utils.credentials.verify_credentials to validate against logged-in user
    :param parent: an optional main window to show modal dialog
    :param default_values: a dict of optional default values for the form. The keys could be "username", "domain" and
    "password". If username or domain are not informed, current logged-in username and domain are used
    :return: a dict with the following keys: username, domain and password if validation was ok
    or an empty dict if user cancelled
    """
    default_values = default_values or dict()
    field_list = [UiField(name="domain", label="Domain",
                          default_value=default_values.get("domain", get_current_domain()),
                          editable=False),
                  UiField(name="username", label="User",
                          default_value=default_values.get("username", get_current_user()),
                          editable=False),
                  UiField(name="password", label="Password",
                          default_value=default_values.get("password", ""),
                          show="*",
                          validation_func=validate_password)]
    return simple_dialog(title, description, field_list, parent=parent)


if __name__ == '__main__':
    # from ong_utils import simple_dialog
    # from ong_utils.ui import UiField, UiFileButton, UiPasswordButton, UiFolderButton

    field_list = [UiField(name="domain",  # Key of the dict in the return dictionary and for validation functions
                          label="Domain",  # Name to the shown for the user
                          default_value="fake domain",  # Default value to be used
                          editable=False  # Not editable
                          ),
                  UiField(name="username", label="User", default_value="fake user",
                          editable=False,
                          ),
                  UiField(name="password", label="Password", default_value="",
                          show="*",  # Hides password by replacing with *
                          # validation_func=verify_credentials
                          # The validation function receives values of all fields, so should accept extra **kwargs
                          button=UiPasswordButton()
                          ),
                  UiField(name="server", label="Server",
                          width=40),
                  # Will ask for a folder and validate that exists
                  UiField(name="folder", label="Folder", button=UiFolderButton(), width=80),
                  # Will ask for a file and validate that exists
                  UiField(name="file", label="File", button=UiFileButton(), width=90),
                  ]
    # Call the function to open the login window with custom options
    res = simple_dialog(title="Sample form", description="Show descriptive message for the user",
                        field_list=field_list)
    print(res)

    res = user_domain_password_dialog("Log in form", "Please enter your credentials",
                                      validate_password=None,
                                      default_values=dict(username="fake user", domain="fake domain",
                                                          password="fake password"))
    print(res)
    # print(tkinter.simpledialog.askstring(title="hola", prompt="di algo",
    #                                      initialvalue="respuesta de ejemplo"))
    # print(tkinter.messagebox.askyesno(title="Hola", message="Dime si o no"))
