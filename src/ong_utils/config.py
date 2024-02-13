import getpass
import logging
import logging.config
import os

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

    def __init__(self, project_name: str, cfg_filename: str = None,
                 default_app_cfg: dict = None, default_log_cfg: dict = None):
        """
        Reads configurations from f"~/.config/ongpi/{project_name}.{extension}"
        :param project_name: the name of the project. Configuration for the project will be read from this key
            in the yaml/json file
        :param cfg_filename: an optional filename for the configuration (including extension). If not informed, the
            filename will be project_name + . + extension, from the known extensions (yaml, yml, json ,js)
        :param default_app_cfg: a dict with a default application configuration
        :param default_log_cfg: a dict with a default logging configuration (logDict format)
        """
        self.project_name = project_name
        self.test_project_name = f"{self.project_name}_test"
        self.__app_cfg = default_app_cfg or dict()
        self.__log_cfg = default_log_cfg or _default_logger_config(app_name=project_name)
        self.config_path = os.path.expanduser(os.environ.get("ONG_CONFIG_PATH",
                                                             os.path.join("~", ".config", "ongpi")))
        self.__test_cfg = dict()
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
                with open(self.config_filename, "r") as f_cfg:
                    cfg = loader(f_cfg)
                if project_name in cfg:
                    self.__app_cfg.update(cfg[self.project_name])
                    self.__test_cfg.update(cfg.get(self.test_project_name) or dict())
                    self.__log_cfg.update(cfg.get("log") or dict())
                    self._fix_logger_config()
                    logging.config.dictConfig(self.__log_cfg)
                    self.__logger = logging.getLogger(self.project_name)
                    break
                else:
                    raise ValueError(f"Key {self.project_name} was not found in config file {self.config_filename}")
            else:
                continue

        if self.config_filename is None:
            self.config_filename = self._get_cfg_filename(list(self.extensions_cfg.keys())[0], filename=cfg_filename)
            self.create_default_config()
            raise FileNotFoundError(f"Configuration file {self.config_filename} not found. "
                                    f"A new one based on default values has been created")

    def _get_cfg_filename(self, ext: str = None, filename: str = None):
        if not filename:
            filename = self.project_name + ext
        return os.path.join(self.config_path, filename)

    def create_default_config(self):
        """Creates a config file with the contents of the current configuration"""
        cfg = {self.project_name: self.__app_cfg, "log": dict()}
        _, ext = os.path.splitext(self.config_filename)
        writer = self.extensions_cfg[ext][1]
        os.makedirs(os.path.dirname(self.config_filename), exist_ok=True)
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
        return self.__logger

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
            self.create_default_config()
        else:
            raise ValueError(f"Item {item} already existed in app config. Edit it manually")


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
