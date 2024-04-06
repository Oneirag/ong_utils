import unittest
import warnings
import tkinter as tk

from ong_utils import simple_dialog, OngFormDialog
from ong_utils.ui import UiField, UiPasswordButton, UiFileButton, UiFolderButton


class TestUI(unittest.TestCase):

    def setUp(self):
        self.dialog = OngFormDialog("Test dialog", "Dialog to test functionality")

    def test_simple_dialog(self):
        """Shows some dialogs to test functionality. Checks that raises deprecation error"""
        warnings.simplefilter("error")      # Forces deprecation warning to be raised as exception
        with self.assertRaises(DeprecationWarning) as dw:
            simple_dialog("Test", "desc", [UiField("name", "label")])
        warnings.simplefilter("default")    # Reverts to default

    def test_simple_dialog_all(self):
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
        simple_dialog("titulo", "descripcion", field_list=field_list)

    def verify_dialog(self, expected=None):
        retval = self.dialog.show()
        self.assertTrue(isinstance(retval, dict), "Invalid return type")
        if expected is not None:
            self.assertEqual(retval, expected)
        if retval:  # If user did not cancel...
            print(retval)
            for field in self.dialog.dict_ui_fields:
                self.assertIn(field, retval,
                              f"field {field} not found")

    def test_simple_dialog_emtpy(self):
        """Shows an empty dialog"""
        self.verify_dialog(expected=dict())

    def test_simple_dialog_one_entry(self):
        """Shows a dialog with just one entry"""
        self.dialog.add_entry_field(name="Field1", label="Example field", default_value="default")
        self.verify_dialog()

    def test_simple_dialog_tooltip(self):
        """Shows a dialog with just one entry"""
        self.dialog.add_entry_field(name="Field1", label="Example field", default_value="default",
                                    description="Example field just for testing")
        self.dialog.add_file_field(name="file", label="File", description="choose a file")
        self.dialog.add_folder_field(name="folder", label="Folder", description="choose a folder")
        self.dialog.add_combo_field(name="combo", label="Combo", valid_values=['one', 'two'],
                                    default_value="three",
                                    description="Choose a value")
        self.dialog.add_boolean_field(name="bool", label="Valid?", default_value=True,
                                      description="Mark to say yes")
        self.verify_dialog()

    def test_simple_dialog_two_entries(self):
        """Shows a dialog with just two entries"""
        (self.dialog.add_entry_field(name="Field2", label="Example field", default_value="default").
         set_focus()
         .add_entry_field(name="Field3", label="Other field", default_value="Other")
         )
        self.verify_dialog()

    def test_simple_dialog_domain_user_password(self):
        """Test that username, password works ok. Validates against current oks"""
        self.dialog.add_domain_user_password()
        self.verify_dialog()

    def test_simple_dialog_duplicated_entries(self):
        """Test that exception is raised in case of duplicated field names"""
        with self.assertRaises(ValueError) as ve:
            self.dialog.add_domain_user_password()
            # It will add again user field, raises error...
            self.dialog.add_user_field()
            self.dialog.show()

    def test_simple_dialog_file_folder(self):
        """Tests file and folder entries of a dialog"""
        self.dialog.add_file_field(name="file", label="File")
        self.dialog.add_folder_field(name="folder", label="Folder")
        self.verify_dialog()

    def test_ong_form_dialog_bool(self):
        for b in True, False:
            self.setUp()
            with self.subTest(bool=b):
                self.dialog.add_boolean_field("bool", f"choose {b}", default_value=b)
                self.verify_dialog(dict(bool=b))


if __name__ == '__main__':
    unittest.main()
