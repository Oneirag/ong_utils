"""
Class to permanently store data using keyring
"""
import os
import keyring
import keyring.errors
import zlib
import base64
import json

def compress_string(input_string):
    # Convert the string to bytes
    input_bytes = input_string.encode('utf-8')

    # Compress the bytes using zlib
    compressed_bytes = zlib.compress(input_bytes)

    # Encode the compressed bytes in base64 to get a UTF-8 encoded string
    compressed_string = base64.b64encode(compressed_bytes).decode('utf-8')

    return compressed_string

def decompress_string(compressed_string):
    # Decode the UTF-8 encoded string into bytes
    compressed_bytes = base64.b64decode(compressed_string.encode('utf-8'))

    # Decompress the bytes using zlib
    decompressed_bytes = zlib.decompress(compressed_bytes)

    # Decode the decompressed bytes back to a string
    decompressed_string = decompressed_bytes.decode('utf-8')

    return decompressed_string


class InternalStorage:

    def __init__(self, app_name: str):
        self.__username = os.getenv("USER", os.getenv("USERNAME"))
        self.__app_name = app_name

    @property
    def username(self) -> str:
        return self.__username

    @property
    def app_name(self) -> str:
        return self.__app_name

    def serialize(self, value) -> str:
        return compress_string(json.dumps(value))

    def deserialize(self, value: str):
        return json.loads(decompress_string(value))

    def store_value(self, key: str, value):
        """Stores something in keyring"""
        store_value = self.serialize(value)
        self.store_value_raw(key, store_value)

    def store_value_raw(self, key: str, value):
        keyring.set_password(self.app_name, key, value)
        assert value == self.get_value_raw(key)

    def get_value_raw(self, key: str):
        return keyring.get_password(self.app_name, key)

    def get_value(self, key: str):
        stored_value = self.get_value_raw(key)
        if stored_value is None:
            return
        original = self.deserialize(value=stored_value)
        return original

    def remove_stored_value(self, key: str):
        try:
            keyring.delete_password(self.app_name, key)
        except keyring.errors.PasswordDeleteError:
            pass


if __name__ == '__main__':
    storage = InternalStorage("Ejemplo")

    for data in ("hola", 1245, dict(uno=1, dos=2),[dict(hola=1, adios=2), 3, ['holi']],
                 "a" * 2000):
        serial = storage.serialize(data)
        data2 = storage.deserialize(serial)
        print(data, data2)
