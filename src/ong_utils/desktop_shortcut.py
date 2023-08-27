"""
Creates a desktop link to launch a certain program,
and modifies its installed files (in dist-info), so it can be uninstalled
"""
import base64
import hashlib
import importlib.metadata
import os
import tempfile
import zipfile
from importlib.metadata import distribution

import pyshortcuts.shortcut
from pyshortcuts import make_shortcut, platform, shortcut, get_folders
from wheel.bdist_wheel import bdist_wheel


def is_pip() -> bool:
    """Returns True if running under pip"""
    if "pip" in os.environ.get("_", ""):
        return True
    else:
        return False


class PipCreateShortcut(bdist_wheel):
    """
    Creates shortcuts for each entry_point when installing the package from git using pip
    """

    def run(self):
        bdist_wheel.run(self)
        impl_tag, abi_tag, plat_tag = self.get_tag()
        archive_basename = f"{self.wheel_dist_name}-{impl_tag}-{abi_tag}-{plat_tag}"
        wheel_path = os.path.join(self.dist_dir, archive_basename + ".whl")
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
        eps = list(ep for ep in self.distribution.entry_points)
        for ep in eps:
            files = list(f for f in ep.dist.files if f.match(ep.name))
            # TODO: test if this script works in windows
            script = os.path.normpath(files[0].locate().as_posix())
            # splits = eps[0].value.split(':')
            # module = splits[0]
            # function = splits[1] if len(splits) > 1 else None
            # if not function:
            #     script = f"_ -m {module}"
            # else:
            #     This DOES NOT WORK at least in mac, no matter if using " or '
            #     script = f'_ -c "from {module} import {function};{function}()"'
            iconfile = 'shovel.icns' if platform.startswith('darwin') else 'shovel.ico'
            name = ep.name
            scut = shortcut(script=script, name=name, userfolders=get_folders())
            scut_filename = os.path.join(scut.desktop_dir, scut.target)
            # Not needed: shortcuts are not overwritten using make_shortcut
            # if os.path.exists(scut_filename):
            #     os.remove(scut_filename)
            scut = make_shortcut(script=script, name=name, icon=None,
                                 description="Lanzador de la interfaz del punteo de cuentas",
                                 startmenu=False)
            retval += "\n".join(file2record(scut_filename))
        return retval


def file2record(filename: str) -> list:
    """Returns a list of lines to append to RECORD file associated to a given a file"""
    if os.path.isfile(filename):
        with open(filename, "r") as f:
            contents = f.read()

        sha256 = base64.urlsafe_b64encode(hashlib.sha256(contents.encode()).digest())[:-1]
        txt_append_record_file = f"{filename},sha256={sha256},{len(contents)}"
        return [txt_append_record_file]
    elif os.path.isdir(filename):
        # This is macos case. Let's see if it can delete whole dir. Works like a charm ;)
        return [f"{filename}, ,"]
    else:
        raise FileNotFoundError(f"Not found file: {filename}")


class ShortCutInstaller:
    def __init__(self, library: str):
        self.library = library
        try:
            self.distribution = distribution(self.library)
        except importlib.metadata.PackageNotFoundError as pnfe:
            pnfe.args = (f"{library}. Is it installed?",)
            raise pnfe

        # gets the record file (if exists)
        records = list(f for f in self.distribution.files if f.name == "RECORD")
        if records:
            self.record = records[0].locate()
        else:
            self.record = None

    def add_file_record(self, shortcut: pyshortcuts.Shortcut):
        """Adds information on a shortcut to the RECORD file (if exists)"""
        append_to_record_file = []
        if self.record is not None:
            filename = shortcut.target
            path = shortcut.desktop_dir
            # path = shortcut.startmenu_dir # In case it was created in start menu
            sc_path = os.path.join(path, filename)
            append2record = file2record(sc_path)
            with open(self.record, "r") as f:
                record_data = f.readlines()
            with open(self.record, "a") as f:
                # avoid writing multiple times in record file
                for line in append2record:
                    if line not in record_data:
                        f.writelines([line])

    def make_shortcut(self, entry_point: str):
        """It just can run the given code if it is a module (runs if __name__ == '__main__' part"""
        eps = list(ep for ep in self.distribution.entry_points if ep.name == entry_point)
        if eps:
            files = list(f for f in eps[0].dist.files if f.match(eps[0].name))
            # TODO: test if this script works in windows
            script = os.path.normpath(files[0].locate().as_posix())
            # splits = eps[0].value.split(':')
            # module = splits[0]
            # function = splits[1] if len(splits) > 1 else None
            # if not function:
            #     script = f"_ -m {module}"
            # else:
            #     This DOES NOT WORK at least in mac, no matter if using " or '
            #     script = f'_ -c "from {module} import {function};{function}()"'
        else:
            script = f"_ -m {entry_point}"
        iconfile = 'shovel.icns' if platform.startswith('darwin') else 'shovel.ico'
        # script = '_ -m liquidaciones.conciliation_gui'
        # script = entry_point

        name = 'Punteo de cuentas'
        scut = shortcut(script=script, name=name, userfolders=get_folders())
        scut_filename = os.path.join(scut.desktop_dir, scut.target)
        # Not needed: shortcuts are not overwritten using make_shortcut
        # if os.path.exists(scut_filename):
        #     os.remove(scut_filename)
        retva = make_shortcut(script=script, name=name, icon=None,
                              description="Lanzador de la interfaz del punteo de cuentas",
                              startmenu=False)

        self.add_file_record(retva)


if __name__ == '__main__':
    # try:
    #     sci = ShortCutInstaller("ong_gesfincas222")
    # except Exception as e:
    #     print(f"CORRECT: exception found {e}")
    sci = ShortCutInstaller("ong_gesfincas")
    sci.make_shortcut("punteo")

"""
flat couch vector, minimalist, in style of SKSKS app icon
"""
