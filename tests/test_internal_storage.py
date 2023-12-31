import unittest
import random
import string

from ong_utils.internal_storage import InternalStorage, InternalStorageV0
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
        self.old_internal_storage = InternalStorageV0(self.app_name)

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

    def test_read_old_values(self):
        """Tests that old InternalStorage values can be read in new storage"""
        value = "Something to write"
        self.old_internal_storage.store_value(self.store_key, value)
        self.assertEqual(value, self.old_internal_storage.get_value(self.store_key),
                         "Value was not properly stored in old storage")
        self.assertEqual(value, self.internal_storage.get_value(self.store_key),
                          "Value in old storage could not be read with new code")
        self.internal_storage.remove_stored_value(self.store_key)
        self.assertIsNone(self.old_internal_storage.get_value(self.store_key),
                          "Deleted value was read in old storage")
        self.assertIsNone(self.internal_storage.get_value(self.store_key),
                          "Deleted value was read in storage")

    def test_read_new_values(self):
        """Tests that new InternalStorage values can NOT be read in old storage"""
        value = "Something to write"
        self.internal_storage.store_value(self.store_key, value)
        self.assertEqual(value, self.internal_storage.get_value(self.store_key),
                          "Value in new storage could not be read with new code")
        self.assertNotEqual(value, self.old_internal_storage.get_value(self.store_key),
                         "Value was not properly stored in old storage")
        self.internal_storage.remove_stored_value(self.store_key)
        self.assertIsNone(self.old_internal_storage.get_value(self.store_key),
                          "Deleted value was read in old storage")
        self.assertIsNone(self.internal_storage.get_value(self.store_key),
                          "Deleted value was read in storage")

    def test_delete_chunks(self):
        """Tests that all chunks are deleted from a certain key"""
        n_chunks = 10
        value = get_random_string(self.internal_storage.chunk_size * n_chunks)
        self.internal_storage.store_value(self.store_key, value)
        self.assertEqual(value, self.internal_storage.get_value(self.store_key),
                         "Value was not properly stored")
        self.internal_storage.remove_stored_value(self.store_key)
        self.assertIsNone(self.internal_storage.get_value(self.store_key),
                          "Value was not properly deleted")
        for idx_chunk in range(n_chunks):
            chunk_name = self.internal_storage.chunk_name(self.store_key, idx_chunk)
            self.assertIsNone(self.internal_storage.get_value(chunk_name),
                              f"Chunk #{idx_chunk} was not deleted")


if __name__ == '__main__':
    unittest.main()
