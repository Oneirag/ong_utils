import unittest

from ong_utils.internal_storage import InternalStorage
from tests import jwt_token


class TestInternalStorage(unittest.TestCase):
    store_values = [
        "This is a string",
        dict(this="is", a="dictionary"),
        "this is a long string" * 100,
        1222322434132343241345541434567876543,
        # Sample JWT token
        jwt_token * 4,
    ]
    store_key = "key_to_delete"

    @property
    def app_name(self):
        return self.__class__.__name__

    def setUp(self):
        self.internal_storage = InternalStorage(self.app_name)
        self.internal_storage.remove_stored_value(self.store_key)

    def tearDown(self):
        self.internal_storage.remove_stored_value(self.store_key)

    def iter_test_values(self):
        """Iterates through all test values creating separated tests"""
        for value in self.store_values:
            with self.subTest(value=value):
                yield value
                pass

    def test_serialize_values(self):
        """Tests that values can be serialized and deserialized without trouble"""
        for value in self.iter_test_values():
            serialized = self.internal_storage.serialize(value)
            recovered = self.internal_storage.deserialize(serialized)
            self.assertEqual(value, recovered)
            self.assertLess(len(serialized), 1025, "Too long data")

    def test_store_values(self):
        """Tests that values can be stored and read from storage without changing"""
        for value in self.iter_test_values():
            self.internal_storage.store_value(self.store_key, value)
            expected = self.internal_storage.serialize(value)
            self.assertEqual(expected, self.internal_storage.get_value_raw(self.store_key))
            stored = self.internal_storage.get_value(self.store_key)
            self.assertEqual(value, stored)
            self.internal_storage.remove_stored_value(self.store_key)

    def test_get_nonexistent_value(self):
        """Tests that if getting a non-existent value there is no exception"""
        for key in self.store_key, "vasdfadfasdafsfd":
            self.internal_storage.remove_stored_value(key)
            value = self.internal_storage.get_value(key)
            self.assertIsNone(value)


if __name__ == '__main__':
    unittest.main()
