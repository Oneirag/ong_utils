"""
Simple ui screens
"""
from __future__ import annotations

import abc
import gettext
import locale
import os.path
import tkinter
import warnings
from dataclasses import dataclass
from functools import partial
from tkinter import filedialog, Menu
from tkinter import ttk, messagebox, END, Toplevel, scrolledtext
from tkinter.simpledialog import Dialog
from typing import List, Callable

import pandas as pd

from ong_utils.utils import get_current_domain, get_current_user
from ong_utils.credentials import verify_credentials
from ong_utils import is_windows, AdditionalRequirementException, raise_extra_install


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
    """Base class for buttons added to a simple dialog (for selecting files or folders, showing passwords...)"""

    def __init__(self, empty_ok: bool = False):
        self.empty_ok = empty_ok
        self.button = None

    @abc.abstractmethod
    def button_name(self) -> str | None:
        return None

    @abc.abstractmethod
    def button_command(self, entry: ttk.Entry):
        """What to do when button is pressed. Receives an entry which is the one that has the attached info"""
        pass

    def make_button(self, master, entry: ttk.Entry) -> ttk.Button:
        self.button = ttk.Button(master, text=self.button_name(), command=partial(self.button_command, entry=entry))
        return self.button

    def validate(self, value: str) -> bool:
        if self.empty_ok and not value:
            return True
        return self.__validate_not_empty(value)

    @abc.abstractmethod
    def __validate_not_empty(self, value: str) -> bool:
        """Validates not emtpy values"""
        return True


class UiFolderButton(_UiBaseButton):
    """Defines a button for browsing for a folder and update entry field accordingly. It also validates
    that the contents of the field is a valid existing folder"""

    def button_name(self) -> str | None:
        return "\u2026"  # Horizontal ellipsis (...)

    def button_command(self, entry: ttk.Entry):
        folder_selected = filedialog.askdirectory(initialdir=entry.get(),
                                                  title=_("Select folder"))
        if folder_selected:
            entry.delete(0, END)
            entry.insert(0, folder_selected)

    def __validate_not_empty(self, value: str) -> bool:
        return os.path.isdir(value)


class UiFileButton(_UiBaseButton):
    """Defines a button for browsing for a file and update entry field accordingly. It also validates
    that the contents of the field is a valid existing file"""

    def __init__(self, filetypes: list = None, empty_ok: bool = False):
        """
        Creates a UiFileButton that validates a file
        :param filetypes: list of tuples with file description, extension. See askopenfilename
        :param empty_ok:
        """
        super().__init__(empty_ok=empty_ok)
        self.filetypes = filetypes

    def button_name(self) -> str | None:
        return "\u2026"  # Horizontal ellipsis (...)

    def button_command(self, entry: ttk.Entry):
        filetypes = self.filetypes if self.filetypes else ()
        file_selected = filedialog.askopenfilename(initialdir=entry.get(),
                                                   title=_("Select file"),
                                                   filetypes=filetypes
                                                   )
        if file_selected:
            entry.delete(0, END)
            entry.insert(0, file_selected)

    def __validate_not_empty(self, value: str) -> bool:
        if self.filetypes:
            if not any(value.lower().endswith(ext.lower[-3:]) for (name, ext) in self.filetypes):
                return False
        return os.path.isfile(value)


class UiPasswordButton(_UiBaseButton):
    """Defines a button for showing/hiding passwords. Does not add additional validations"""

    view = True
    show = None
    eye_on = "\U0001F441"  # An eye
    # eye_off = "\U0000274C"  # A cross
    eye_off = "\U0001F441\u0336\u0336\u0336\u0336\u0336\u0336"  # An eye with a cross

    def button_name(self) -> str | None:
        return self.eye_on

    def button_command(self, entry: ttk.Entry):
        if self.view:
            self.button.configure(text=self.eye_off)
            self.show = entry.cget("show")
            entry.configure(show="")
        else:
            self.button.configure(text=self.eye_on)
            entry.configure(show=self.show)
        self.view = not self.view

    def __validate_not_empty(self, value: str) -> bool:
        return True


@dataclass
class UiField:
    name: str  # Name of the field (for internal code)
    label: str  # Label of the field (that will be shown in the window and translated)
    default_value: str | bool = ""  # Default value
    show: str = None  # For passwords use "*"
    # Validation function, that will receive all field names of the window, so need **kwargs
    validation_func: Callable[[dict], bool] = None
    # Validation error message, an extra, descriptibe message for the user when validation fails
    validation_error_message: str = None
    # state of the tk.Entry. True is editable, false will make not editable
    editable: bool = True
    # Width parameter of an Entry field, make it longer if needed
    width: int = 20
    # Include an additional Button
    button: _UiBaseButton = None
    # True to avoid validation when field is empty (defaults to False)
    allow_empy: bool = False
    # Optional list of valid values. If supplied, a ComboBox is used instead of an Entry Field
    valid_values: List[str] = None
    # Description: a str to show additional info to the user on the field
    description: str = None
    # Height of the field. If above 1, creates a scrollText field
    height: int = 1

    @property
    def state(self):
        """Turns editable into the string state parameter of the tk.Entry"""
        return _STATE_ENABLED if self.editable else _STATE_DISABLED

    @property
    def is_boolean(self) -> bool:
        """Returns True if has valid values, only two and boolean"""
        if self.valid_values:
            return sorted(list(self.valid_values)) == sorted([True, False])
        return False


class _UiFieldButton(UiField):
    @abc.abstractmethod
    def button_command(self, entry: ttk.Entry):
        print("Executing parent command")
        pass

    @abc.abstractmethod
    def button_name(self) -> str:
        pass


class _SimpleDialog(Dialog):
    def __init__(self, title: str, description: str, field_list: List[UiField], parent=None,
                 focus_field: UiField = None, create_batch: bool=False):
        self.description = description
        self.field_list = field_list
        self.__values = dict()
        self.ui_fields = dict()
        self.variables = dict()
        self.validated = False
        self.focus_field = focus_field
        self.tooltip = None
        self.parent = parent
        self.create_batch = create_batch
        super().__init__(self.parent, title)

    def show_tooltip(self, event=None):
        """Shows a tooltip with the field.description content. Widget is received from event.widget"""
        widget = event.widget
        field = list(field for f, field in zip(self.ui_fields.values(), self.field_list)
                     if f is widget)[0]
        text = field.description
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25

        self.tooltip = Toplevel(widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(self.tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1,
                          font=("Arial", "12", "normal"))
        label.pack(ipadx=2)

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()

    def body(self, master):
        """Creates ui elements for the body, returns the one that will take focus"""
        description_label = ttk.Label(master, text=self.description)
        description_label.grid(row=0, column=0, pady=5, padx=10, columnspan=2)
        focus = description_label
        for row, field in enumerate(self.field_list):
            # Label and entry for the username
            label = ttk.Label(master, text=_(field.label))
            label.grid(row=row + 1, column=0, pady=5, padx=10, sticky="w")
            if field.valid_values:
                if field.is_boolean:
                    """
                    Checkbutton does not work properly, so a workaround is made here
                    Works nice with BooleanVar but that does not work when parent=None
                    Here works without variables: uses an internal boolean that changes
                    when toggling and creates a fake get() function to work as the rest
                    of the ttk elements
                    """
                    entry = ttk.Checkbutton(master, width=field.width,
                                            onvalue=True, offvalue=False,
                                            text="",  # To disable text box in windows
                                            )
                    # get function does not exit, inject it
                    entry.bool = field.default_value
                    entry.state([("" if entry.bool else "!") + "selected !alternate"])
                    entry.invoke()
                    entry.invoke()

                    def toggle(cb: ttk.Checkbutton):
                        cb.bool = not cb.bool
                        print(f"toggled to {cb.bool}")

                    entry.configure(command=partial(toggle, cb=entry))
                    entry.get = lambda: entry.bool

                else:
                    entry = ttk.Combobox(master, show=field.show, width=field.width,
                                         values=field.valid_values,
                                         # textvariable=self.variables[field.name]
                                         )
                    if field.default_value in field.valid_values:
                        entry.set(field.default_value)
            else:
                if field.height <= 1:
                    entry = ttk.Entry(master, show=field.show, width=field.width,
                                      #textvariable=self.variables[field.name]
                                      )
                    entry.insert(0, field.default_value)
                else:
                    entry = scrolledtext.ScrolledText(master, show=field.show, width=field.width,
                                                      wrap=tkinter.WORD, height=field.height)
                    entry.insert("1.0", field.default_value)

            if not field.editable:
                # entry.configure(state='readonly')
                entry.configure(state=_STATE_DISABLED)
            entry.grid(row=row + 1, column=1, pady=5, padx=(10, 10), sticky="w")
            if field.button:
                btn = field.button.make_button(master, entry)
                btn.grid(row=row + 1, column=1, pady=5, padx=(0, 10), sticky="e")
            if field.description:
                entry.bind("<Enter>", self.show_tooltip)
                entry.bind("<Leave>", self.hide_tooltip)

            self.ui_fields[field.name] = entry
            if not self.focus_field:
                focus = entry
            elif field is self.focus_field:
                focus = entry
        if self.create_batch:
            self.create_batch_menu()
        return focus

    def buttonbox(self):
        super().buttonbox()
        # Removes bind on return to allow adding more lines if height > 1
        for field in self.field_list:
            if field.height > 1:
                self.unbind("<Return>")

    def create_batch_menu(self) -> None:
        """Creates a menu for the form that is able to read an Excel sheet. Needs additional libraries"""
        try:
            import pandas as pd
        except ImportError:
            raise_extra_install("xlsx")
        # Adds two additional buttons, one for read XLS one for write
        menubar = Menu(self, tearoff=0)
        batch_menu = Menu(menubar, tearoff=0)
        batch_menu.add_cascade(label="Create XLSX template", command=self.handle_write_xls)
        batch_menu.add_separator()
        batch_menu.add_cascade(label="Read XLSX batch", command=self.handle_read_xls)
        menubar.add_cascade(menu=batch_menu, label="Batch")
        self.config(menu=menubar)

    def handle_read_xls(self):
        """Opens an Excel sheet, reads all rows and for each row create a dict so retval will be a list of dicts"""
        filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        retval = []
        if filename:
            df = pd.read_excel(filename, index_col=None)
            if diff := set(self.ui_fields.keys()).difference(df.columns):
                messagebox.showerror(_("Error"), f"File {filename} does not contain the following required columns "
                                                 f"{diff}")
                return
            for idx, row in df.iterrows():
                values = {k: row[k] for k in self.ui_fields.keys()}
                self.__values = values
                if not self.validate(update_values=False):
                    return
                retval.append(values)
            self.__values = retval
            self.withdraw()
            self.update_idletasks()
            self.cancel()

    def handle_write_xls(self):
        """Writes an empty Excel file to serve as template for inserting many values"""
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if filename:
            try:
                df = pd.DataFrame(columns=list(self.ui_fields.keys()))
                df.to_excel(filename, index=False)
            except Exception as e:
                messagebox.showerror(_("Error"), f"File {filename} could not be written. Reason: {e}")

    def validate(self, update_values: bool = True):
        """Validates form, returning 1 if ok and 0 otherwise. Shows error messages if it does not work"""
        try:
            if update_values:
                self.update_values()
            for field in self.field_list:
                # Do not validate if field is empty and allow_empty = True
                if field.allow_empy and not self.__values[field.name]:
                    continue
                try:
                    if ((field.validation_func and not field.validation_func(**self.__values)) or
                            field.button and not field.button.validate(self.__values[field.name])):
                        error_msg = _("Invalid field") + ": " + _(field.label)
                        if field.validation_error_message:
                            error_msg += f"\n{field.validation_error_message}"
                        messagebox.showerror(_("Error"), error_msg)
                        return 0
                except AdditionalRequirementException as are:
                    messagebox.showerror(_("Error"), _("Additional requirements for validating field") + f": {are}")
                except Exception as e:
                    messagebox.showerror(_("Error"),f"{e}")
            self.validated = True
            return 1
        except Exception as e:
            print(e)
            return 0

    def update_values(self):
        for field in self.field_list:
            # self.__values[field.name] = self.variables.get(field.name).get() if field.name in self.variables else None
            if field.name not in self.ui_fields:
                field_value = None
            else:
                ui_field = self.ui_fields.get(field.name)
                if not isinstance(ui_field, scrolledtext.ScrolledText):
                    field_value = ui_field.get()
                else:
                    field_value = ui_field.get("1.0", "end-1c")
            self.__values[field.name] = field_value
    @property
    def return_values(self) -> dict:
        """Returns a dict of field names and values, or an empty dict if validation failed"""
        if self.validated:
            return self.__values
        else:
            return dict()


class OngFormDialog:
    """
    Shows a Form dialog to enter values for several fields, one per row.
    Given title, and description and fields and returns a dict with
    the values. You need to invoke the "show" method for the window to
    show and return values.
    It has chained functions to create the form field elements needed.
    Examples
        # Emtpy dialog
        OngFormDialog("Empty dialog", "Empty description").show()
        # Dialog to ask for a string, returns a dict with "value" as key if user accepted
        # or empty dict if user cancelled
        OngFormDialog("title", "desc").add_entry("value", "Enter something:")
    """

    def __init__(self, title: str, description: str, parent=None):
        """Creates an empty dialog only with title and description"""
        self.title = title
        self.description = description
        self.parent = parent
        self.dict_ui_fields = None
        self.focus_field = None
        self.clear()

    def __get_uifield(self, field_name: str) -> UiField | None:
        """Returns a UiField. if field_name is None, returns the last one. If no fields, return None"""
        last_field = None
        if self.dict_ui_fields:
            if field_name is None or field_name not in self.dict_ui_fields:
                last_field = list(self.dict_ui_fields.values())[-1]
            else:
                last_field = self.dict_ui_fields[field_name]
        return last_field

    def __update_uifield(self, field_name: str | None, property: str, value):
        if not self.dict_ui_fields:
            return
        last_field = self.__get_uifield(field_name)
        setattr(last_field, property, value)

    def __append_uifield(self, uifield: UiField):
        if uifield.name in self.dict_ui_fields:
            raise ValueError(f"Duplicated field name: {uifield.name}")
        self.dict_ui_fields[uifield.name] = uifield

    def add_domain_field(self, default_value: str = None,
                         editable: bool = False):
        """Creates a domain field named "domain" and labeled 'Domain'. By default,
        it is filled with current domain of the computer and it is not editable"""
        name = "domain"
        label = "Domain"
        default_value = default_value if default_value is not None else get_current_domain()
        return self.add_entry_field(name=name, label=label, default_value=default_value, editable=editable)

    def add_user_field(self, default_value: str = None, editable: bool = False):
        """Creates a domain field, named "username", labeled 'User'. By default,
        it is filled with current login user of the computer and it is not editable"""
        name = "username"
        label = "User"
        default_value = default_value if default_value is not None else get_current_user()
        return self.add_entry_field(name=name, label=label, default_value=default_value, editable=editable)

    def add_password_field(self, default_value: str = "", validate_os: bool = True):
        """Creates a password field. By default, it is named "password", labeled 'Password',
        is editable and validates against the OS. If you don't want password to be validated,
        call afterward add_validation with None"""
        name = "password"
        label = "Password"
        self.add_entry_field(name=name, label=label, default_value=default_value, editable=True)
        bullet = "\u2022"  # specifies bullet character
        self.__update_uifield(None, "show", bullet)
        self.__set_button(UiPasswordButton())
        if validate_os:
            self.__update_uifield(None,"validation_func", verify_credentials)
        return self

    def add_domain_user_password(self, default_domain: str = None, default_user: str = None,
                                 default_password: str = None, validate_os: bool = True):
        """Adds a domain, user and password field. By default, with the current login data
        and validated against the current OS"""
        self.add_domain_field(default_value=default_domain)
        self.add_user_field(default_value=default_user)
        self.add_password_field(default_value=default_password)
        if not validate_os:
            self.set_validation(None)
        return self

    def add_file_field(self, name: str, label: str, default_value: str = None, filetypes: list = None,
                       empty_ok: bool = False, width: int = 70):
        """adds a field to select a file, including a button to navigate files"""
        self.add_entry_field(name=name, label=label, default_value=default_value, editable=True)
        self.set_width(width)
        self.__set_button(UiFileButton(empty_ok=empty_ok, filetypes=filetypes))
        return self

    def add_folder_field(self, name: str, label: str, default_value: str = None,
                         empty_ok: bool = False, width: int = 70):
        """adds a field to select a folder, including a button to navigate folders"""
        self.add_entry_field(name=name, label=label, default_value=default_value, editable=True)
        self.set_width(width)
        self.__set_button(UiFolderButton(empty_ok=empty_ok))
        return self

    def add_combo_field(self, name: str, label: str, valid_values: list, default_value: str = None,
                        editable: bool = True):
        """Creates a combo box, with the list of strings for valid values and the default
        value. If default value not in valid_values, the first value will be used"""
        if default_value not in valid_values:
            default_value = valid_values[0]
        field = UiField(name=name, label=label, default_value=default_value,
                        valid_values=valid_values,
                        editable=editable)
        self.__append_uifield(field)
        return self

    def add_boolean_field(self, name: str, label: str, default_value: bool = True,
                          editable: bool = True):
        """Creates a combo field with two values (true/false), that is evaluated as boolean"""
        self.add_combo_field(name, label, valid_values=[True, False], default_value=default_value,
                             editable=editable)
        return self

    def add_entry_field(self, name: str, label: str, default_value: str = "",
                        editable: bool = True):
        """
        Adds a simple entry field for strings, with no validations
        :param name: the name of the field in the return dictionary
        :param label: the label to be shown in the field
        :param default_value: default value (a string). Defaults to empty string
        :param editable: True (default) to make the field editable
        :return: self to chain
        """
        field = UiField(name=name, label=label, default_value=default_value or "",
                        editable=editable)
        self.__append_uifield(field)
        return self

    def set_show(self, show: str, field_name: str = None):
        """Changes the show property of a ui element"""
        self.__update_uifield(field_name, "show", show)
        return self

    def set_tooltip(self, tooltip: str, field_name: str = None):
        """Defines a tooltip message for the given element (defaults to last one)"""
        self.__update_uifield(field_name, "description", tooltip)
        return self

    def set_validation(self, validation_func, field_name: str = None, validation_error_message: str = None):
        """Adds a validation func to the last added field, overriding any default validation"""
        self.__update_uifield(field_name, "validation_func", validation_func)
        self.__update_uifield(field_name, "validation_error_message", validation_error_message)
        return self

    def set_validation_single(self, validation_func: Callable, field_name: str = None,
                              validation_error_message: str = None):
        """
        Adds a validation func that only relies on in the values of this field
        :param validation_func: it takes one parameter "value" and returns True or False
        :param field_name: optional field name to apply validation. Defaults to last available field
        :param validation_error_message: extra, informative message for the user when validation fails
        :return: self
        """
        last_field = self.__get_uifield(field_name)

        def new_validation_func(last_field=last_field, **kwargs):
            return validation_func(kwargs[last_field.name])

        self.set_validation(new_validation_func, field_name, validation_error_message)
        return self

    def set_focus(self, field_name: str = None):
        """Mark last added field as the one that will have focus"""
        if self.dict_ui_fields:
            self.focus_field = self.__get_uifield(field_name)
        return self

    def set_width(self, width: int, field_name: str = None):
        """Changes the width of the last element. Returns self to chain"""
        self.__update_uifield(field_name, "width", width)
        return self

    def set_height(self, height: int, field_name: str = None):
        """Changes height of the last element. If height > 1, then a scrolled text is created"""
        self.__update_uifield(field_name, "height", height)
        return self

    def __set_button(self, button: _UiBaseButton):
        self.__update_uifield(None, "button", button)
        return self

    def clear(self):
        """Clears all form fields. Can be chained"""
        self.dict_ui_fields = dict()
        self.focus_field = None
        return self

    def show(self, title: str=None, description: str=None, show_batch: bool=False) -> dict | list:
        """Shows the dialog and return values. Can override title and description from constructor"""
        win = _SimpleDialog(title=title or self.title, description=description or self.description,
                            field_list=list(self.dict_ui_fields.values()),
                            parent=self.parent, focus_field=self.focus_field,
                            create_batch=show_batch)
        return win.return_values

    def show_batch(self, title: str=None, description: str=None) -> dict | list:
        """Shows dialog with the batch menu and potentially returns a list of dicts"""
        return self.show(title=title, description=description, show_batch=True)


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

    Use the UiPasswordButton, UiFolderButton or UiFileButton as the button parameter to add a button
    to show password or to select and validate files or folders, such as here:
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
    """
    warnings.warn("This function is deprecated and will be removed in next versions."
                  "Use OngSimpleDialog instead", DeprecationWarning)
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
    bullet = "\u2022"  # specifies bullet character

    field_list = [UiField(name="domain", label="Domain",
                          default_value=default_values.get("domain", get_current_domain()),
                          editable=False),
                  UiField(name="username", label="User",
                          default_value=default_values.get("username", get_current_user()),
                          editable=False),
                  UiField(name="password", label="Password",
                          default_value=default_values.get("password", ""),
                          show=bullet,
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
                          # validation_func=
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

    res = simple_dialog("Un titulo",
                        "una Descripcion",
                        field_list=
                        [
                            UiField(name="a", label="A", allow_empy=True, button=UiFileButton()),
                            UiField(name="b", label="B", default_value="Si", valid_values=['Si', 'No'])
                        ])
    print(res)
