import unittest
import warnings

from ong_utils import simple_dialog, OngFormDialog, get_current_user, get_current_domain, verify_credentials
from ong_utils.ui import UiField, UiPasswordButton, UiFileButton, UiFolderButton


class TestUI(unittest.TestCase):

    def setUp(self):
        self.dialog = OngFormDialog("Test dialog", "Dialog to test functionality")

    def test_simple_dialog(self):
        """Shows some dialogs to test functionality. Checks that raises deprecation error"""
        warnings.simplefilter("error")  # Forces deprecation warning to be raised as exception
        with self.assertRaises(DeprecationWarning) as dw:
            simple_dialog("Test", "desc", [UiField("name", "label")])
        warnings.simplefilter("default")  # Reverts to default

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

    def verify_dialog(self, expected=None, new_title: str = None, new_description: str = None):
        retval = self.dialog.show(title=new_title, description=new_description)
        self.assertTrue(isinstance(retval, dict), "Invalid return type")
        if expected is not None and retval:
            for k, v in expected.items():
                self.assertEqual(retval[k], v, f"Unexpected value for field {k}")
        if retval:  # If user did not cancel...
            print(retval)
            for field in self.dialog.dict_ui_fields:
                self.assertIn(field, retval,
                              f"field {field} not found")

    def test_ong_form_dialog_emtpy(self):
        """Shows an empty dialog"""
        self.verify_dialog(expected=dict(), new_description="Test of empty form with no fields")

    def test_ong_form_dialog_one_entry(self):
        """Shows a dialog with just one entry"""
        self.dialog.add_entry_field(name="Field1", label="Example field", default_value="default")
        self.verify_dialog(new_description="Form with single entry")

    def test_ong_form_dialog_tooltip(self):
        """Shows a dialog with any kind of field that can have tooltips"""
        self.dialog.add_entry_field(name="Field1", label="Example field", default_value="default").set_tooltip(
            "Example field just for testing"
        )
        self.dialog.add_file_field(name="file", label="File").set_tooltip("choose a file")
        self.dialog.add_folder_field(name="folder", label="Folder").set_tooltip("choose a folder")
        self.dialog.add_combo_field(name="combo", label="Combo", valid_values=['one', 'two'],
                                    default_value="three").set_tooltip("Choose a value")
        self.dialog.add_boolean_field(name="bool", label="Valid?", default_value=True).set_tooltip(
            "Mark to say yes")
        self.verify_dialog(new_description="Test of tooltip functionallity")

    def test_ong_form_dialog_two_entries(self):
        """Shows a dialog with just two entries"""
        (self.dialog.add_entry_field(name="Field2", label="Example field", default_value="default").
         set_focus()
         .add_entry_field(name="Field3", label="Other field", default_value="Other")
         )
        self.verify_dialog(new_description="Test of two entry fields")

    def test_ong_form_dialog_domain_user_password(self):
        """Test that username, password works ok. Validates against current oks"""
        self.dialog.add_domain_user_password()
        self.verify_dialog(new_description="Test of domain/user/password with system validation")

    def test_ong_form_dialog_domain_user_password_no_validation(self):
        """Test that username, password works ok. It does NOT validate against current oks"""
        self.dialog.add_domain_user_password().set_validation(None)
        self.verify_dialog(new_description="Test of domain/user/password WITHOUT system validation")

    def test_ong_form_dialog_duplicated_entries(self):
        """Test that exception is raised in case of duplicated field names"""
        with self.assertRaises(ValueError) as ve:
            self.dialog.add_domain_user_password()
            # It will add again user field, raises error...
            self.dialog.add_user_field()
            self.dialog.show()

    def test_ong_form_dialog_file_folder(self):
        """Tests file and folder entries of a dialog"""
        self.dialog.add_file_field(name="file", label="File")
        self.dialog.add_folder_field(name="folder", label="Folder")
        self.verify_dialog(new_description="Test file and folder fields")

    def test_ong_form_dialog_bool(self):
        for b in True, False:
            self.dialog.clear()
            with self.subTest(bool=b):
                self.dialog.add_boolean_field("bool", f"choose {b}", default_value=b)
                self.verify_dialog(dict(bool=b),
                                   new_description=f"Test boolean field with {b} as default")

    def test_ong_form_dialog_validation(self):
        """Test that a simple validation works"""

        def validation(**kwargs) -> bool:
            return kwargs['test'] == "test"

        self.dialog.add_entry_field(name="test", label="Only test allowed").set_tooltip(
            "You can only write test here").set_validation(validation)
        self.dialog.add_entry_field(name="test2", label="Say whatever").set_tooltip(
            "You can insert whatever value here")

        self.verify_dialog(dict(test="test"), new_description="Test validation of single field")

    def test_ong_form_dialog_validation_single(self):
        """Test that a simple validation works"""

        self.dialog.add_entry_field(name="test", label="Only test allowed",
                                    default_value="write test").set_tooltip(
            "You can only write test here")
        self.dialog.set_validation_single(lambda x: x == "test")
        self.dialog.add_entry_field(name="test2", label="Say whatever").set_tooltip(
            "You can ony insert 'whatever'  here")
        self.dialog.set_validation_single(lambda y: y == "whatever")

        self.verify_dialog(dict(test="test", test2="whatever"),
                           new_description="Test validation of values of single field")

    def test_readme_md(self):
        """Test that code for readme.md works ;)"""
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
            validation_func=verify_credentials
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
            print(res)  # Dict with the results

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
        print(result)

    def test_batch_dialog(self):
        """Tests that show batch works properly"""
        result = self.dialog.add_entry_field(name="example", label="Example").\
            add_entry_field(name="other", label="Other").show_batch()
        print(result)
        self.assertTrue(isinstance(result, list))

    def test_multiline_dialog(self):
        """Tests that a multiline dialog works properly"""
        default_value = "\n".join(["this", "is", "a", "test"])
        self.dialog.add_entry_field(name="data", label="data", default_value=default_value).\
            set_height(height=8)
        self.dialog.add_entry_field(name="url", label="Url")
        result = self.dialog.show()
        print(result)
        self.assertTrue(isinstance(result, dict))
        self.assertSequenceEqual(result['data'], default_value)


if __name__ == '__main__':
    unittest.main()
