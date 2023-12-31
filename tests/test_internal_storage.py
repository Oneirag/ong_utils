import unittest
import random
import string

from ong_utils.internal_storage import InternalStorage
from tests import jwt_token


def get_random_string(length) -> str:
    # choose from all ascii letter
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    # print("Random string of length", length, "is:", result_str)
    return result_str


class TestInternalStorage(unittest.TestCase):
    store_values = [
        "This is a string",
        dict(this="is", a="dictionary"),
        "this is a long string" * 100,
        1222322434132343241345541434567876543,
        # Sample JWT token
        jwt_token * 4,
        # Quite long string, it must be a list, not a tuple
        [
            [dict(name=get_random_string(10), value=get_random_string(256)) for _ in range(10)],
            get_random_string(500)
        ],
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

    def iter_test_values(self, target_idx=None):
        """Iterates through all test values creating separated tests"""
        for idx, value in enumerate(self.store_values):
            if target_idx is not None and idx != target_idx:
                continue
            with self.subTest(value=value):
                yield value
                pass

    def test_serialize_values(self):
        """Tests that values can be serialized and deserialized without trouble"""
        for value in self.iter_test_values():
            serialized = self.internal_storage.serialize(value)
            recovered = self.internal_storage.deserialize(serialized)
            self.assertEqual(value, recovered)
            # self.assertLess(len(serialized), 1025, "Too long data")

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
