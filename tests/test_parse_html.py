from unittest import TestCase
from ong_utils import find_js_variable


class Test(TestCase):
    source = """
    <html>
    <script>
    variable_0="some_value_0";
    variable_1 = "some_value_1";
    dict = {"key_1": "some_value_2", "key_2":"some_value_3"}
    </script>
    <body>
    <a alt="bla bla" href = "http://somewhere.com"> link text </a>
    </body>
    </html>
    """

    def test_find_js_variable(self):

        for variable_name, separator, expected_value in [
            ("variable_0", "=", "some_value_0"),
            ("variable_1", "=", "some_value_1"),
            ('key_1', ":", "some_value_2"),
            ('key_2', ":", "some_value_3"),
            ("non_existing", ":", None),

        ]:
            with self.subTest(variable_name=variable_name, separator=separator):
                found = find_js_variable(self.source, variable_name, separator)
                self.assertEqual(expected_value, found)

