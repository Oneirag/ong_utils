"""
Base class to use Office Automation. Creates the corresponding office app, cleans cache if needed and
exits properly discarding changes
"""
from ong_utils.import_utils import raise_extra_exception
try:
    from win32com import client, __gen_path__
except ModuleNotFoundError:
    raise_extra_exception("office")
from pathlib import Path
import re
from shutil import rmtree
from abc import abstractmethod


class _OfficeBase:
    """
    Base class for automation of office applications under windows.
    """
    @property
    @abstractmethod
    def client_name(self) -> str:
        """This must return the client_name for EnsureDispatch, such as Excel.Application or Word.Application"""
        return ""

    def __init__(self, logger=None):
        self.logger = logger
        self.__client = None

    @property
    def client(self):
        """Initializes client"""
        if self.__client is not None:
            return self.__client
        try:
            self.__client = client.gencache.EnsureDispatch(self.client_name)
            if hasattr(self.__client, "Visible"):
                self.__client.Visible = True
        except AttributeError as e:
            # Sometimes we might have to clean the cache to open
            m_failing_cache = re.search(r"win32com\.gen_py\.([\w\-]+)", str(e))
            if m_failing_cache:
                cache_folder_name = m_failing_cache.group(1)
                if self.logger is not None:
                    self.logger.warning(f"Cleaning cache for '{cache_folder_name}'")
                cache_folder = Path(__gen_path__).joinpath(cache_folder_name)
                rmtree(cache_folder)
                self.__client = client.gencache.EnsureDispatch(self.client_name)
            else:
                raise
        finally:
            return self.__client

    def quit(self):
        """Exits discarding changes"""
        if self.__client:
            if self.client_name.startswith("Excel"):
                self.__client.DisplayAlerts = False
                self.__client.Quit()
            elif self.client_name.startswith("Word"):
                self.__client.Quit(SaveChanges=False)
            else:
                # In PowerPoint this could make a message to be shown if presentations are not saved before closing
                self.__client.Quit()

    def __del__(self):
        """Exits discarding changes"""
        self.quit()


class ExcelBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Excel.Application"


class WordBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Word.Application"


class AccessBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Access.Application"


class PowerpointBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "PowerPoint.Application"


class OutlookBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Outlook.Application"


