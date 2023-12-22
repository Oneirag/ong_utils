"""
Class to permanently store data using keyring
"""
import os
import urllib.parse
import keyring
import keyring.errors
import pickle
import gzip


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

    @property
    def encoding(self) -> str:
        return "iso-8859-1"

    def serialize(self, value) -> str:
        value_pickle = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        zipped = gzip.compress(value_pickle)
        # return zipped.decode(self.encoding)
        value = urllib.parse.quote(zipped.decode(self.encoding))
        return value

    def deserialize(self, value: str):
        value = urllib.parse.unquote(value).encode(self.encoding)
        unzipped = gzip.decompress(value)
        unpickled = pickle.loads(unzipped)
        return unpickled

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
