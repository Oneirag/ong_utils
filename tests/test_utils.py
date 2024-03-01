import unittest

from ong_utils.utils import is_mac, is_linux, is_windows, is_debugging


class TestUtils(unittest.TestCase):

    def test_platform_identification(self):
        """Test that platform identification works properly as variable or function"""
        platforms = [is_mac, is_linux, is_windows]
        platform_var = [variable for variable in platforms if variable]
        platform_func = [func for func in platforms if func()]
        self.assertEqual(len(platform_var), 1)
        self.assertEqual(len(platform_func), 1)
        self.assertEqual(platform_func[0], platform_var[0])
        print(f"You are running {platform_func[0].platform_name}")

    def test_debugging(self):
        """Test that debugging identification works as variable or function"""
        bool_debug = True if is_debugging else False
        self.assertEqual(is_debugging, is_debugging())
        self.assertEqual(is_debugging, bool_debug)
        self.assertEqual(is_debugging(), bool_debug)
        if is_debugging:
            print("Debugging")
        else:
            print("Not debugging")


if __name__ == '__main__':
    unittest.main()
