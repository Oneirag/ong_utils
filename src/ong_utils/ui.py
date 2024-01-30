"""
Simple ui screens
"""
import gettext
import locale
from dataclasses import dataclass
from tkinter import ttk, messagebox
from tkinter.simpledialog import Dialog
from typing import List, Callable

from ong_utils.credentials import verify_credentials
from ong_utils.utils import get_current_user, get_current_domain

# Configure localization
locale.setlocale(locale.LC_ALL, "")  # Use the system's default locale
lang = locale.getlocale()[0]
translation = gettext.translation("messages", localedir="locales", languages=[lang], fallback=True)
translation.install()

# Define _() as the translation function
_ = translation.gettext


@dataclass
class UiField:
    name: str  # Name of the field (for internal code)
    label: str  # Label of the field (that will be shown in the window and translated)
    default_value: str = ""  # Default value
    show: str = None  # For passwords use "*"
    # Validation function, that will receive all field names of the window, so need **kwargs
    validation_func: Callable[[dict], bool] = None
    # state of the tk.Entry. Use "DISABLED" to make an element not editable
    state: str = "NORMAL"


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
        for row, field in enumerate(field_list):
            # Label and entry for the username
            label = ttk.Label(master, text=_(field.label))
            label.grid(row=row + 1, column=0, pady=5, padx=10, sticky="w")
            entry = ttk.Entry(master, show=field.show, state=field.state)
            entry.insert(0, field.default_value)
            entry.grid(row=row + 1, column=1, pady=5, padx=(10, 10))
            self.ui_fields[field.name] = entry
            focus = entry
        return focus

    def validate(self):
        """Validates form, returning 1 if ok and 0 otherwise. Shows error messages if it does not work"""
        try:
            self.update_values()
            for field in field_list:
                if field.validation_func:
                    if not field.validation_func(**self.__values):
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
        """Returns a dict of field names and values, or a empty dict if validation failed"""
        if self.validated:
            return self.__values
        else:
            return dict()


def simple_dialog(title: str, description: str, field_list: List[UiField], parent=None) -> dict:
    """Shows a dialog with the given title, and description and fields and returns a dict with
    the values.
    Example: field_list = [UiField(name="domain", label="Domain", default_value="homecomputer"),
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
                                parent=None) -> dict:
    """A window that asks for username, domain and password, and validates it. Returns a dict
    with username, domain and password"""
    field_list = [UiField(name="domain", label="Domain", default_value=get_current_domain(), state="DISABLED"),
                  UiField(name="username", label="User", default_value=get_current_user(), state="DISABLED"),
                  UiField(name="password", label="Password", default_value="",
                          show="*",
                          validation_func=validate_password)]
    return simple_dialog(title, description, field_list, parent=parent)


if __name__ == '__main__':
    field_list = [UiField(name="domain", label="Domain", default_value=get_current_domain()),
                  UiField(name="username", label="User", default_value=get_current_user()),
                  UiField(name="password", label="Password", default_value="",
                          show="*",
                          validation_func=verify_credentials),
                  UiField(name="server", label="Servidor")]
    # Call the function to open the login window with custom options
    # res = dialog(title="Password", description="Pon aqui tu titulo que espero que sea largo",
    #                    field_list=field_list)
    # print(res)
    #
    res = user_domain_password_dialog("Logueate", "no se guarda nada",
                                      validate_password=verify_credentials)
    print(res)
