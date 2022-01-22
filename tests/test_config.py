from ong_utils import OngConfig
import os
import yaml
import unittest
import tempfile


class TestConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cfg_filename = os.path.join(cls.temp_dir.name, "example.yaml")
        app_name = "test_case"
        # Create emtpy config
        with open(cfg_filename, "w") as f:
            yaml.dump({app_name: []}, f)
        print(cfg_filename)
        cls.cfg = OngConfig(app_name, cfg_filename=cfg_filename)
        cls.config = cls.cfg.config

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
        print(fc := self.get_config_text())
        # Try to redefine value...must raise exception
        self.assertRaises(ValueError, self.cfg.add_app_config, non_existing_key, "Another value")
        # File content must remain unchanged
        self.assertEqual(fc, self.get_config_text(), "Configuration has been changed!")

    def get_config_text(self) -> str:
        """Gets contents of config filename"""
        with open(self.cfg.config_filename, "r") as f:
            fc = f.read()
        return fc

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()


if __name__ == '__main__':
    unittest.main()