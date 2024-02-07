"""
Base class to use Office Automation. Creates the corresponding office app, cleans cache if needed and
exits properly discarding changes
"""
import os.path

from ong_utils.import_utils import raise_extra_exception

try:
    from win32com import client, __gen_path__
except ModuleNotFoundError:
    raise_extra_exception("office")
from pathlib import Path
import re
from shutil import rmtree
from abc import abstractmethod
from functools import wraps


def fix_filename(method):
    @wraps(method)
    def _impl(self, filename, *method_args, **method_kwargs):
        filename = os.path.abspath(filename)
        method_output = method(self, filename, *method_args, **method_kwargs)
        return method_output

    return _impl


class _OfficeBase:
    """
    Base class for automation of office applications under windows.
    """

    @property
    @abstractmethod
    def client_name(self) -> str:
        """This must return the client_name for EnsureDispatch, such as Excel.Application or Word.Application"""
        return ""

    def __init__(self, logger=None, quit_on_exit: bool = True):
        """Creates an office instance, with an optional logger and closing or not client on exit"""
        self.logger = logger
        self.__client = None
        self.file = None
        self.__quit_on_exit = quit_on_exit

    @abstractmethod
    def open(self, filename: str):
        """Opens a file from given path"""
        pass

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
            # Close file if already opened, discarding changes
            if self.file:
                if self.client_name.startswith("PowerPoint"):
                    self.file.Close()
                else:
                    self.file.Close(False)
                self.file = None
            if self.client_name.startswith("Excel"):
                self.__client.DisplayAlerts = False
                self.__client.Quit()
            elif self.client_name.startswith("Word"):
                self.__client.Quit(SaveChanges=False)
            else:
                # In PowerPoint this could make a message to be shown if presentations are not saved before closing
                self.__client.Quit()
            self.__client = None

    def __del__(self):
        """Exits discarding changes, if quit_on_exit was True in class constructor"""
        if self.__quit_on_exit:
            try:
                self.quit()
            except Exception as e:
                # exception could be risen if there are other opened documents not saved
                print(e)
                pass


class ExcelBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Excel.Application"

    @fix_filename
    def open(self, filename: str):
        self.file = self.client.Workbooks.Open(filename)


class WordBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Word.Application"

    @fix_filename
    def open(self, filename: str):
        """Opens a word document"""
        self.file = self.client.Documents.Open(filename)


class AccessBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Access.Application"

    @fix_filename
    def open(self, filename: str):
        self.file = self.client.OpenCurrentDatabase(filename)


class PowerpointBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "PowerPoint.Application"

    @fix_filename
    def open(self, filename: str):
        """Opens a ppt filename"""
        self.file = self.client.Presentations.Open(FileName=filename, WithWindow=1)


class OutlookBase(_OfficeBase):
    @property
    def client_name(self) -> str:
        return "Outlook.Application"

    def open(self, filename: str):
        """Does nothing: opening outlook documents makes no sense"""
        pass
