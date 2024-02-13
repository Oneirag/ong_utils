"""
Creates a desktop link to launch a certain program,
and modifies its installed files (in dist-info), so it can be uninstalled
"""
from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import inspect
import os
import sys
import tempfile
import zipfile
from importlib.metadata import distribution

from ong_utils.import_utils import raise_extra_exception
try:
    import pyshortcuts.shortcut
    from pyshortcuts import make_shortcut, platform, shortcut, get_folders
    from wheel.bdist_wheel import bdist_wheel
except ModuleNotFoundError:
    raise_extra_exception("shortcuts")


def is_pip() -> bool:
    """Returns True if running under pip"""
    if "pip" in os.environ.get("_", ""):
        return True
    else:
        return False


def get_name_script(entry_points) -> list:
    """
    Takes a distribution object and returns a list of tuples for each entry point with the script name and the
    module to be executed
    Example: for "script1 = package.file:function" [("script1", "package.file")]
    :param entry_points: the list of entry points (result of  self.distribution.entry_points)
    :return:
    """
    retval = []

    def script_to_shortcut(script):
        script = script.split(":")[0]
        # check that script is not the one currently executing
        stack = inspect.stack()
        script_os = script.replace(".", os.sep)
        if not any(script_os in s.filename for s in stack):
            return f"_ -m {script}"
        else:
            return None

    if isinstance(entry_points, dict):
        for console_script in entry_points.get("console_scripts", []):
            name, script = map(str.strip, console_script.split("="))
            script = script_to_shortcut(script)
            if script:
                retval.append((name, script))
    else:
        for ep in entry_points:
            script = script_to_shortcut(ep.value)
            if script:
                retval.append((ep.name, script))
    return retval


class PipCreateShortcut(bdist_wheel):
    """
    Creates shortcuts for each entry_point when installing the package from git using pip
    """

    def run(self):
        bdist_wheel.run(self)
        if not is_pip():
            # If not running under pip, do nothing, as results could be strange
            return
        impl_tag, abi_tag, plat_tag = self.get_tag()
        archive_basename = f"{self.wheel_dist_name}-{impl_tag}-{abi_tag}-{plat_tag}"
        wheel_path = os.path.join(self.dist_dir, archive_basename + ".whl")
        ####
        # Create a new wheel, by unzipping the original files but the RECORD file, that will be modified with the new
        # shortcut files, in order to be uninstalled later
        ####
        tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(wheel_path))
        os.close(tmpfd)
        # create a temp copy of the archive without filename
        with zipfile.ZipFile(wheel_path, 'r') as zin:
            with zipfile.ZipFile(tmpname, 'w') as zout:
                zout.comment = zin.comment  # preserve the comment
                for item in zin.infolist():
                    if not item.filename.endswith("RECORD"):
                        zout.writestr(item, zin.read(item.filename))
                    else:
                        # Write custom record file here
                        data = zin.read(item.filename)
                        data += self.append_scut_record().encode()
                        zout.writestr(item, data)
        # replace with the temp archive
        os.remove(wheel_path)
        os.rename(tmpname, wheel_path)

    def append_scut_record(self) -> str:
        """Creates a shortcut for every entry point"""
        retval = ""
        for name, script in get_name_script(self.distribution.entry_points):
            iconfile = 'shovel.icns' if platform.startswith('darwin') else 'shovel.ico'
            # Not needed: shortcuts are not overwritten using make_shortcut
            # scut = shortcut(script=script, name=name, userfolders=get_folders())
            # if os.path.exists(scut_filename):
            #     os.remove(scut_filename)
            scut = make_shortcut(script=script, name=name, icon=None,
                                 description="",
                                 startmenu=False)
            scut_filename = os.path.join(scut.desktop_dir, scut.target)
            for record in file2record(scut_filename):
                retval += f"{record}\n"
        return retval


def file2record(filename: str) -> list:
    """Returns a list of lines to append to RECORD file associated to a given a file"""
    if os.path.isfile(filename):
        with open(filename, "rb") as f:
            contents = f.read()
        sha256 = base64.urlsafe_b64encode(hashlib.sha256(contents).digest())[:-1].decode("utf-8")
        txt_append_record_file = f"{filename},sha256={sha256},{len(contents)}"
        return [txt_append_record_file]
    elif os.path.isdir(filename):
        # This is macos case. Let's see if it can delete whole dir. Works like a charm ;)
        return [f"{filename}, ,"]
    else:
        raise FileNotFoundError(f"Not found file: {filename}")


class PostInstallCreateShortcut:
    def __init__(self, library: str = __name__):
        self.library = library
        try:
            self.distribution = distribution(self.library)
            print(f"Creating shortcuts for {library} installed in {self.distribution._path}")
        except importlib.metadata.PackageNotFoundError as pnfe:
            pnfe.args = (f"{library}. Is it installed?",)
            raise pnfe

        # gets the record file (if exists)
        records = list(f for f in self.distribution.files if f.name == "RECORD")
        if records:
            self.record = records[0].locate()
            self.installed_files = None
        else:
            # Add to installed files of the egg_file
            egg_dir = self.distribution._path.as_posix()
            assert (egg_dir.endswith("egg-info"))
            self.installed_files = os.path.join(egg_dir, "installed_files.txt")
            self.record = None

    def add_file_record(self, shortcut: pyshortcuts.Shortcut):
        """Adds information on a shortcut to the RECORD file (if exists), including icon"""
        append_to_record_file = []
        output_file = self.record or self.installed_files
        filename = shortcut.target
        path = shortcut.desktop_dir
        # path = shortcut.startmenu_dir # In case it was created in start menu
        sc_path = os.path.join(path, filename)
        icon_path = shortcut.icon if not "pyshorcuts" in shortcut.icon else ""
        for file in (sc_path, icon_path):
            if not file:
                continue
            append2record = file2record(file)
            if os.path.exists(output_file):
                with open(output_file, "r") as f:
                    record_data = f.readlines()
            else:
                record_data = ""
            with open(output_file, "a") as f:
                # avoid writing multiple times in record file
                for line in append2record:
                    if output_file == self.installed_files:
                        line = line.split(",")[0]
                    if line not in record_data:
                        f.write(line + "\n")

    def find_icon(self, script_name) -> str | None:
        """Finds an icon for the given file. If found in png format, then transformed to ico/icns format.
        Returns None if not found"""

        iconfile_ext = '.icns' if platform.startswith('darwin') else '.ico'
        # Try to find icon in "icons" folder
        icon = script_name + iconfile_ext
        iconfile = list(f for f in self.distribution.files if f.name.endswith(icon))
        if not iconfile:
            # Try to find icon in png format
            png_file = list(f for f in self.distribution.files if f.name.endswith(script_name + ".png"))
            if not png_file:
                iconfile = None
            else:
                png_file = png_file[0].locate().as_posix()
                iconfile = png_file[:-4] + iconfile_ext
                # Create the ad hoc ico/icns file
                if sys.platform == "darwin":
                    import icnsutil
                    img = icnsutil.IcnsFile()
                    img.add_media('ic07', file=png_file)
                    img.write(iconfile)
                else:
                    from PIL import Image
                    img = Image.open(png_file)
                    img.save(iconfile)
                pass
        else:
            iconfile = iconfile[0].locate().as_posix()
        return iconfile

    def make_shortcuts(self):
        for name, script in get_name_script(self.distribution.entry_points):
            # files = list(f for f in entry_point.dist.files)
            # TODO: test if this script works in windows
            # script = os.path.normpath(files[0].locate().as_posix())
            # splits = eps[0].value.split(':')
            # module = splits[0]
            # function = splits[1] if len(splits) > 1 else None
            # if not function:
            # else:
            #     This DOES NOT WORK at least in mac, no matter if using " or '
            #     script = f'_ -c "from {module} import {function};{function}()"'
            iconfile = self.find_icon(name)
            scut = shortcut(script=script, name=name, userfolders=get_folders(), icon=iconfile)
            scut_filename = os.path.join(scut.desktop_dir, scut.target)
            # In order to add icons once installed, overwrite the shorcut anyway
            # if os.path.exists(scut_filename):
            #     continue  # If shortcut existed, skip
            retva = make_shortcut(script=script, name=name, icon=iconfile,
                                  description="",
                                  startmenu=False)

            self.add_file_record(retva)


if __name__ == '__main__':
    sci = PostInstallCreateShortcut()
    sci.make_shortcuts()

"""
flat couch vector, minimalist, in style of SKSKS app icon
"""
