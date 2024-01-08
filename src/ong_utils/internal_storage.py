"""
Class to permanently store data using keyring
"""
import base64
import json
import zlib
from textwrap import wrap

import keyring
import keyring.errors


def compress_string(input_string: str) -> str:
    """Compresses a string into another string utf-8 encoded"""
    # Convert the string to bytes
    input_bytes = input_string.encode('utf-8')

    # Compress the bytes using zlib
    compressed_bytes = zlib.compress(input_bytes)

    # Encode the compressed bytes in base64 to get a UTF-8 encoded string
    compressed_string = base64.b64encode(compressed_bytes).decode('utf-8')

    return compressed_string


def decompress_string(compressed_string: str) -> str:
    """Decompresses a utf-8 encoded string into another string utf-8 encoded"""

    # Decode the UTF-8 encoded string into bytes
    compressed_bytes = base64.b64decode(compressed_string.encode('utf-8'))

    # Decompress the bytes using zlib
    decompressed_bytes = zlib.decompress(compressed_bytes)

    # Decode the decompressed bytes back to a string
    decompressed_string = decompressed_bytes.decode('utf-8')

    return decompressed_string


class InternalStorageBase:
    def __init__(self, app_name: str):
        self.__app_name = app_name

    @property
    def app_name(self) -> str:
        return self.__app_name

    def serialize(self, value) -> str:
        """Serializes and compresses an object into a string."""
        return compress_string(json.dumps(value))

    def deserialize(self, value: str):
        """Deserializes and decompresses a string into is original value"""
        if value is None:
            return None
        return json.loads(decompress_string(value))

    def store_value_raw(self, key: str, value):
        keyring.set_password(self.app_name, key, value)
        assert value == InternalStorageBase(self.app_name).get_value_raw(key)

    def get_value_raw(self, key: str):
        return keyring.get_password(self.app_name, key)

    def remove_stored_value(self, key: str):
        try:
            keyring.delete_password(self.app_name, key)
        except keyring.errors.PasswordDeleteError:
            pass


class InternalStorageV0(InternalStorageBase):

    @property
    def version(self):
        return 0

    def make_header(self, chunks: int = 0) -> dict:
        return dict(version=self.version, class_name=self.__class__.__name__, chunks=chunks)

    def serialize(self, value) -> str:
        """Serializes and compresses an object into a string."""
        return compress_string(json.dumps(value))

    def deserialize(self, value: str):
        """Deserializes and decompresses a string into is original value"""
        if value is None:
            return None
        try:
            retval = json.loads(decompress_string(value))
            return retval
        except:
            return None

    def store_value(self, key: str, value):
        """Stores something in keyring"""
        store_value = self.serialize(value)
        self.store_value_raw(key, store_value)

    def get_value(self, key: str):
        stored_value = self.get_value_raw(key)
        if stored_value is None:
            return
        original = self.deserialize(value=stored_value)
        return original


class InternalStorageV1(InternalStorageV0):
    chunk_size = 1000
    chunk_header_key = "chunks"

    @property
    def version(self):
        return 1

    def chunk(self, store_value: str) -> list:
        """Splits a string into parts of a maximum size"""
        return wrap(store_value, self.chunk_size)

    def store_value_raw(self, key: str, value):
        chunks = self.chunk(value)
        header = self.make_header(chunks=len(chunks))
        super().store_value_raw(key, self.serialize(header))
        for chunk_key, chunk_value in zip(self.iter_chunk_keys(key), chunks):
            super().store_value_raw(chunk_key, chunk_value)

    def chunk_name(self, key: str, idx_chunk: int) -> str:
        return f"{key}_{idx_chunk}"

    def iter_chunk_keys(self, key: str) -> str:
        """Return a list of chunk keys associated to the header found"""
        header = self.deserialize(super().get_value_raw(key))
        if self.header_valid(header):
            for idx_chunk in range(header['chunks']):
                yield self.chunk_name(key, idx_chunk)

    def get_value_raw(self, key: str):
        header = self.deserialize(super().get_value_raw(key))
        if not self.header_valid(header):
            return super().get_value_raw(key)
        raw_values = list()
        for chunk_key in self.iter_chunk_keys(key):
            raw_value = super().get_value_raw(chunk_key)
            if raw_value is None:
                return None
            raw_values.append(raw_value)
        return "".join(raw_values)

    def remove_stored_value(self, key: str):
        """Removes values stored under key (header + all chunks)"""
        for chunk_key in self.iter_chunk_keys(key):
            super().remove_stored_value(chunk_key)
        return super().remove_stored_value(key)

    def header_valid(self, header) -> bool:
        """True if a header is valid (is a dict, with the needed keys and the expected values"""
        if isinstance(header, dict):
            if header.keys() == self.make_header().keys():
                if (header['version'] == self.version and
                        header['class_name'] == self.__class__.__name__):
                    return True
        return False


InternalStorage = InternalStorageV1

if __name__ == '__main__':
    storage = InternalStorage("Ejemplo")

    for data in ("hola", 1245, dict(uno=1, dos=2), [dict(hola=1, adios=2), 3, ['holi']],
                 "a" * 2000):
        serial = storage.serialize(data)
        data2 = storage.deserialize(serial)
        print(data, data2)
