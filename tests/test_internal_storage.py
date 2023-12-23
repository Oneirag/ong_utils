import unittest

from ong_utils.internal_storage import InternalStorage


class TestInternalStorage(unittest.TestCase):
    store_values = [
        "This is a string",
        dict(this="is", a="dictionary"),
        "this is a long string" * 100,
        1222322434132343241345541434567876543,
        # Sample JWT token
        (
            "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJjbGllbnRfaWQiOiJZekV6TUdkb01ISm5PSEJpT0cxaWJEaHlOVEE9IiwicmVzcG9uc2Vf"
            "dHlwZSI6ImNvZGUiLCJzY29wZSI6ImludHJvc2NwZWN0X3Rva2VucywgcmV2b2tlX3Rva2Vu"
            "cyIsImlzcyI6ImJqaElSak0xY1hwYWEyMXpkV3RJU25wNmVqbE1iazQ0YlRsTlpqazNkWEU9"
            "Iiwic3ViIjoiWXpFek1HZG9NSEpuT0hCaU9HMWliRGh5TlRBPSIsImF1ZCI6Imh0dHBzOi8v"
            "bG9jYWxob3N0Ojg0NDMve3RpZH0ve2FpZH0vb2F1dGgyL2F1dGhvcml6ZSIsImp0aSI6IjE1"
            "MTYyMzkwMjIiLCJleHAiOiIyMDIxLTA1LTE3VDA3OjA5OjQ4LjAwMCswNTQ1In0."
            "IxvaN4ER-PlPgLYzfRhk_JiY4VAow3GNjaK5rYCINFsEPa7VaYnRsaCmQVq8CTgddihEPPXe"
            "t2laH8_c3WqxY4AeZO5eljwSCobCHzxYdOoFKbpNXIm7dqHg_5xpQz-YBJMiDM1ILOEsER8A"
            "DyF4NC2sN0K_0t6xZLSAQIRrHvpGOrtYr5E-SllTWHWPmqCkX2BUZxoYNK2FWgQZpuUOD55H"
            "fsvFXNVQa_5TFRDibi9LsT7Sd_az0iGB0TfAb0v3ZR0qnmgyp5pTeIeU5UqhtbgU9RnUCVmG"
            "IK-SZYNvrlXgv9hiKAZGhLgeI8hO40utfT2YTYHgD2Aiufqo3RIbJA"
        ) * 4
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
