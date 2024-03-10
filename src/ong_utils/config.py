import getpass
import logging
import logging.config
import os
import warnings

import keyring
import ujson
import yaml

_missing = object()  # In order to use None as default value for function args, this value must be used


class OngConfig:
    extensions_cfg = {
        '.yaml': (yaml.safe_load, yaml.dump),
        '.yml': (yaml.safe_load, yaml.dump),
        '.json': (ujson.load, ujson.dump),
        '.js': (ujson.load, ujson.dump),
    }

    # Static configurations to be shared among different files
    __app_cfg_global = dict()
    __log_cfg_global = dict()
    __test_cfg_global = dict()

    __logger = dict()

    # Setters and getters for accessing to the app, log and test config
    @property
    def __app_cfg(self) -> dict:
        return self.__app_cfg_global[self.project_name]

    @__app_cfg.setter
    def __app_cfg(self, value: dict):
        self.__app_cfg_global[self.project_name] = value

    @property
    def __test_cfg(self) -> dict:
        return self.__test_cfg_global[self.project_name]

    @__test_cfg.setter
    def __test_cfg(self, value: dict):
        self.__test_cfg_global[self.project_name] = value

    @property
    def __log_cfg(self) -> dict:
        return self.__log_cfg_global[self.project_name]

    @__log_cfg.setter
    def __log_cfg(self, value: dict):
        self.__log_cfg_global[self.project_name] = value

    def __init__(self, project_name: str, cfg_filename: str = None,
                 default_app_cfg: dict = None, default_log_cfg: dict = None,
                 default_test_cfg: dict = None, write_default_file: bool = False):
        """
        Reads configurations from f"~/.config/ongpi/{project_name}.{extension}"
        :param project_name: the name of the project. Configuration for the project will be read from this key
            in the yaml/json file
        :param cfg_filename: an optional filename for the configuration (including extension). If not informed, the
            filename will be project_name + . + extension, from the known extensions (yaml, yml, json ,js)
        :param default_app_cfg: a dict with a default application configuration
        :param default_log_cfg: a dict with a default logging configuration (logDict format)
        :param default_test_cfg: a dict with a default test configuration
        :param write_default_file: if False (default), raises Exception if default file is not found. If True
         and default_app_cfg is not None, writes a default file in case it does not exit and continues with default
         values
        """
        self.project_name = project_name
        self.test_project_name = f"{self.project_name}_test"
        self.config_path = os.path.expanduser(os.environ.get("ONG_CONFIG_PATH",
                                                             os.path.join("~", ".config", "ongpi")))
        self.__app_cfg = default_app_cfg or dict()
        self.__test_cfg = default_test_cfg or dict()
        self.__log_cfg = default_log_cfg or _default_logger_config(app_name=self.project_name)
        self.config_filename = None
        for ext, (loader, _) in self.extensions_cfg.items():
            if cfg_filename:
                if cfg_filename.endswith(ext):
                    config_filename = self._get_cfg_filename(filename=cfg_filename)
                else:
                    continue
            else:
                config_filename = self._get_cfg_filename(ext=ext)
            if os.path.isfile(config_filename):
                self.config_filename = config_filename
                if self.read_config_file():
                    break
                else:
                    raise ValueError(f"Key {self.project_name} was not found in config file {self.config_filename}")
            else:
                continue

        if self.config_filename is None:
            self.config_filename = self._get_cfg_filename(list(self.extensions_cfg.keys())[0], filename=cfg_filename)
            self.save()
            # In case there is a default app config and file must not be overwritten, it does not raise an
            # exception and continues normally creating a file with default values
            if default_app_cfg is not None and write_default_file:
                return
            else:
                raise FileNotFoundError(f"Configuration file {self.config_filename} not found. "
                                        f"A new one based on default values has been created")

    def read_config_file(self) -> bool:
        """Reads config file stored in self.config_filename.
        Returns True if file contains required config for self.project_name, False otherwise"""
        cfg = self.load()
        if self.project_name in cfg:
            self.__app_cfg.update(cfg[self.project_name])
            self.__test_cfg.update(cfg.get(self.test_project_name) or dict())
            if self.project_name not in self.__logger:       # Update logger config just in case is not already initialized
                self.__log_cfg.update(cfg.get("log") or dict())
                self._fix_logger_config()
                logging.config.dictConfig(self.__log_cfg)
                self.__logger[self.project_name] = logging.getLogger(self.project_name)
            return True
        else:
            return False

    def _get_cfg_filename(self, ext: str = None, filename: str = None):
        if not filename:
            filename = self.project_name + ext
        return os.path.join(self.config_path, filename)

    def load(self) -> dict | None:
        """Loads contents of self.config_filename. Returns None if file does not exist,
        a dictionary otherwise"""
        ext = os.path.splitext(self.config_filename)[-1]
        loader, writer = self.extensions_cfg[ext]
        if os.path.isfile(self.config_filename):
            with open(self.config_filename, "r") as f_cfg:
                cfg = loader(f_cfg)
                return cfg
        return None

    def create_default_config(self):
        """Creates a config file with the contents of the current configuration"""
        warnings.warn("The use of create_default_config() is deprecated, use save() instead", DeprecationWarning)
        self.save()

    def save(self):
        """Saves current config to the config file self.config_filename"""
        cfg = {self.project_name: self.__app_cfg,
               self.test_project_name: self.__test_cfg, "log": dict()}
        _, ext = os.path.splitext(self.config_filename)
        loader, writer = self.extensions_cfg[ext]
        os.makedirs(os.path.dirname(self.config_filename), exist_ok=True)
        if os.path.isfile(self.config_filename):
            cfg = self.load()
            cfg[self.project_name] = self.__app_cfg
            cfg[self.test_project_name] = self.__test_cfg
        with open(self.config_filename, "w") as f_cfg:
            writer(cfg, f_cfg)

    def _fix_logger_config(self):
        """Replaces log_filename with the current project name, creates directories  for file logs if they don't
        exist and renames logger to self.project_name"""
        log_filename = self.__log_cfg['handlers']['logfile']['filename']
        log_filename = os.path.expanduser(log_filename)
        self.__log_cfg['handlers']['logfile']['filename'] = log_filename
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)

    @property
    def logger(self):
        return self.__logger.get(self.project_name, None)

    def config(self, item: str, default_value=_missing):
        """Checks for a parameter in the configuration, and raises exception if not found.
        If not found but a non-None default_value is used, then default value is returned and no Exception raised"""
        if item in self.__app_cfg:
            return self.__app_cfg[item]
        elif default_value is not _missing:
            return default_value
        else:
            raise ValueError(f"Item {item} not defined in section {self.project_name} of file {self.config_filename}")

    def config_test(self, item: str, default_value=_missing):
        """Checks for a parameter in the configuration in the test section, and raises exception if not found.
        If not found but a non-None default_value is used, then default value is returned and no Exception raised"""
        if item in self.__test_cfg:
            return self.__test_cfg[item]
        elif default_value is not _missing:
            return default_value
        else:
            raise ValueError(f"Item {item} not defined in section {self.test_project_name} "
                             f"of file {self.config_filename}")

    def get_password(self, service_cfg_key: str, username_cfg_key: str):
        """
        Returns a password stored in the keyring for the provided service and username config keys
        :param service_cfg_key: the key of the config item storing the service name, to be retrieved by calling self.config.
        if not found in config, defaults to service_cfg_key
        :param username_cfg_key: the key of the config item storing the username, to be retrieved by calling self.config)
        :return: the password (None if not set)
        """
        return keyring.get_password(self.config(service_cfg_key, service_cfg_key),
                                    self.config(username_cfg_key, username_cfg_key))

    def set_password(self, service_cfg_key: str, username_cfg_key: str) -> None:
        """
        Prompts user for a password to be stored in the keyring for the provided service and username config keys
        :param service_cfg_key: the key of the config item storing the service name (retrieved by calling self.config)
        :param username_cfg_key: the key of the config item storing the username (retrieved by calling self.config)
        :return: None
        """
        password = getpass.getpass()
        return keyring.set_password(self.config(service_cfg_key, service_cfg_key),
                                    self.config(username_cfg_key, username_cfg_key), password)

    def add_app_config(self, item: str, value):
        """Adds a new value to app_config and stores it. Raises value error if item already existed"""
        if item not in self.__app_cfg:
            self.__app_cfg[item] = value
            self.save()
        else:
            raise ValueError(f"Item {item} already existed in app config. Edit it manually")

    def update_app_config(self, item: str, value):
        """Updates a value into app_config and stores it. Raises value error if item did not exist"""
        if item in self.__app_cfg:
            self.__app_cfg[item] = value
            self.save()
        else:
            raise ValueError(f"Item {item} already did not existed in app config.")

    def close_handlers(self, remove_handlers: bool = True):
        """Forces close of handlers, and also remove them if remove_handlers=True (default)"""
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            if remove_handlers:
                self.logger.removeHandler(handler)


def _default_logger_config(app_name: str):
    log_cfg = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default_formatter': {
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
            },
            'detailed_formatter': {
                'format': '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s: %(message)s',
                'datefmt': '%Y-%m-%d %I:%M:%S'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default_formatter',
                'level': 'INFO'
            },
            'logfile': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': f'~/.log/{app_name}.log',  # Filename be formatted later replacing app_name placeholder
                'maxBytes': 10 * 1024 * 1024,
                'backupCount': 5,
                'formatter': 'detailed_formatter'
            },
        },
        'loggers': {
            app_name: {
                'handlers': ['console', 'logfile'],
                'level': 'DEBUG',
                'propagate': True,
            },
        }
    }

    return log_cfg
