import os
import tempfile
import unittest
from unittest.mock import patch

import keyring
import yaml

from ong_utils import OngConfig


def read_file(filename: str) -> str:
    """Gets contents of config filename (opens file and returns read())"""
    with open(filename, "r") as f:
        fc = f.read()
    return fc


class TestConfig(unittest.TestCase):
    service_name = "test_service_name_none_should_reuse_ever"
    user_name = "test_user_name_none_should_reuse_ever"
    sample_key = "a_key"
    sample_value = "a_value"
    sample_config_dict = {sample_key: sample_value}

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.cfg_filename = os.path.join(cls.temp_dir.name, "example.yaml")
        cls.non_existing_cfg_file = os.path.join(cls.temp_dir.name, "non_existing.yaml")
        cls.app_name = "test_case"
        # Create emtpy config
        with open(cls.cfg_filename, "w") as f:
            # yaml.dump({cls.app_name: []}, f)
            # cfg_content = yaml.dump({cls.app_name: {}})
            cfg_content = yaml.dump({cls.app_name: cls.sample_config_dict, "log": {},
                                     cls.app_name + "_test": cls.sample_config_dict})
            f.write(cfg_content)
            print(cfg_content)
        print(cls.cfg_filename)

        cls.cfg = OngConfig(cls.app_name, cfg_filename=cls.cfg_filename)
        cls.logger = cls.cfg.logger
        cls.config = cls.cfg.config
        cls.log_filename = cls.cfg._OngConfig__log_cfg['handlers']['logfile']['filename']

    def test_missing_values(self):
        """Checks management of missing values in config"""
        non_existing_key = "example_value"
        # Exception should be risen here
        self.assertRaises(ValueError, self.config, non_existing_key)
        # Exception should NOT be risen here, as a default value is provided
        _ = self.config(non_existing_key, None)
        # Add the non-existing value to config and now exception must not be risen anymore
        self.cfg.add_app_config(non_existing_key, None)
        _ = self.config(non_existing_key)
        # Print config file contents
        print(fc := read_file(self.cfg.config_filename))
        # Try to redefine value...must raise exception
        self.assertRaises(ValueError, self.cfg.add_app_config, non_existing_key, "Another value")
        # File content must remain unchanged
        self.assertEqual(fc, read_file(self.cfg.config_filename), "Configuration has been changed!")

    @patch("getpass.getpass")
    def test_keyring(self, getpass):
        """Test get_password and set_password. Creates a password, checks that can be read, asks for a new one, prints
        it and finally deletes it"""
        getpass.return_value = "silly_password"
        username_key = "username"
        service_key = "service"
        username = self.config(username_key, None)
        if username is None:
            self.cfg.add_app_config(username_key, self.user_name)
            self.cfg.add_app_config(service_key, self.service_name)
        simpliest_password = "1234"
        keyring.set_password(self.service_name, self.user_name, simpliest_password)
        self.assertEqual(simpliest_password, self.cfg.get_password(service_key, username_key))
        self.cfg.set_password(service_key, username_key)
        print("New password is {}".format(self.cfg.get_password(service_key, username_key)))
        keyring.delete_password(self.service_name, self.user_name)

    def test_log(self):
        """Tests that once a log file has been created, new logs are appended to it. It is not thread safe
        and clears any other log"""
        test_message = "This is an example that must be kept next time logger is executed"
        print(f"{self.log_filename=}")
        if os.path.isfile(self.log_filename):
            contents = read_file(self.log_filename)
            print(contents)
            if contents:
                # Create an empty log file (deleting existing, if any)
                open(self.log_filename, "w").close()
                self.assertFalse(test_message in contents, "Log was not properly deleted")

        # Log a test message
        self.logger.info(test_message)
        # Log file should exist
        self.assertTrue(os.path.isfile(self.log_filename), "Log was not written to file!")
        # Log file contents must be the message created
        self.assertEqual(len(read_file(self.log_filename).splitlines()), 1, "Log was not written to file")
        # now create another instances of cfg and print into log
        num_others = 2
        for _ in range(num_others):
            new_cfg = OngConfig(self.app_name, self.cfg_filename)
            new_cfg.logger.info(test_message)
            del new_cfg  # destroy object, just in case
        contents = read_file(self.log_filename)
        lines = contents.splitlines()
        print(contents)
        self.assertEqual(len(lines), num_others + 1, "Not all logs where written")
        self.assertTrue(all(test_message in line for line in lines), "Incorrect log")

    def test_config_test(self):
        """Tests that config_test function works properly"""
        test = self.cfg.config_test
        retval = test(self.sample_key)
        self.assertEqual(retval, self.sample_value)
        self.logger.info(f"{test(self.sample_key)=}")

    def test_multiple_instances(self):
        """Tests that multiple instances of config share the same data"""
        new_instance = OngConfig(cfg_filename=self.cfg_filename, project_name=self.app_name)
        new_key = "new_key"
        new_value = "sample new value"
        self.assertIsNone(self.config(new_key, default_value=None),
                          f"Key '{new_key}' already existed")
        new_instance.add_app_config(new_key, new_value)
        self.assertEqual(self.cfg.config(new_key), new_value,
                         "Instances do not share same data")

    def test_non_existing_file(self):
        """Test if config for non_existing file works"""
        # When a config is created from a non-existing file, it should raise an exception
        with self.assertRaises(FileNotFoundError) as fnfe:
            OngConfig(self.app_name, cfg_filename=self.non_existing_cfg_file,
                      default_app_cfg=self.sample_config_dict)
        # As in the previous step file is created, config should be read normally now
        new_cfg = OngConfig(self.app_name, cfg_filename=self.non_existing_cfg_file)
        # Test that config is correct
        self.assertEqual(new_cfg.config(self.sample_key), self.sample_value)
        # Now, delete config file and try to create config from default values
        # without raising exception
        os.remove(self.non_existing_cfg_file)
        # this time exception should be not risen
        new_cfg = OngConfig(self.app_name, cfg_filename=self.non_existing_cfg_file,
                            default_app_cfg=self.sample_config_dict,
                            write_default_file=True)
        # Test that config is correct
        self.assertEqual(new_cfg.config(self.sample_key), self.sample_value)

    def test_add_update_keys_config(self):
        """Test to add and update keys in the config file"""
        new_key = "new key"
        new_value = "new value"
        brand_new_value = "brand new value"
        # As the key is not existing, now a value error should be risen
        with self.assertRaises(ValueError) as ve:
            self.cfg.config(new_key)
        # Exception should be risen: value does not yet exist
        with self.assertRaises(ValueError) as ve:
            self.cfg.update_app_config(new_key, new_value)
        self.cfg.add_app_config(new_key, new_value)
        self.assertEqual(self.cfg.config(new_key), new_value)
        # Exception should be risen: value already exists
        with self.assertRaises(ValueError) as ve:
            self.cfg.add_app_config(new_key, new_value)
        # Update value
        self.cfg.update_app_config(new_key, brand_new_value)
        self.assertEqual(self.cfg.config(new_key), brand_new_value)
        # Test persistence: a new config should get the brand new value
        new_cfg = OngConfig(self.app_name, cfg_filename=self.cfg_filename)
        self.assertEqual(new_cfg.config(new_key), brand_new_value)

    @classmethod
    def tearDownClass(cls) -> None:
        # Close handler loggers to allow deleting logging file
        cls.cfg.close_handlers(remove_handlers=True)

        # Delete log file
        os.remove(cls.log_filename)
        cls.temp_dir.cleanup()


if __name__ == '__main__':
    unittest.main()
