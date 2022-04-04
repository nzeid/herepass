"""
Copyright (c) 2022 Nader G. Zeid

This file is part of HerePass.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with HerePass. If not, see <https://www.gnu.org/licenses/gpl.html>.
"""

import pkgutil

from herepass_ui import HerePassUI
from pyinstaller_heartbeat import start_pyinstaller_heartbeat


def print_pyinstaller_bloat():
    # For pyinstaller pruning:
    all_imports = []
    for i in pkgutil.iter_modules():
        all_imports.append(i[1])
    all_imports.sort()

    minimum_imports = [
        "Crypto",
        "__future__",
        "_aix_support",
        "_asyncio",
        "_bootsubprocess",
        "_codecs_cn",
        "_codecs_hk",
        "_codecs_iso2022",
        "_codecs_jp",
        "_codecs_kr",
        "_codecs_tw",
        "_collections_abc",
        "_compat_pickle",
        "_contextvars",
        "_ctypes",
        "_decimal",
        "_hashlib",
        "_json",
        "_multiprocessing",
        "_opcode",
        "_py_abc",
        "_pydecimal",
        "_queue",
        "_strptime",
        "_sysconfigdata__x86_64-linux-gnu",
        "_threading_local",
        "_uuid",
        "_weakrefset",
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "base64",
        "bisect",
        "calendar",
        "codecs",
        "collections",
        "colorsys",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "ctypes",
        "dataclasses",
        "datetime",
        "decimal",
        "dis",
        "email",
        "encodings",
        "enum",
        "fnmatch",
        "functools",
        "genericpath",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "hashlib",
        "heapq",
        "herepass",
        "herepass_ui",
        "hmac",
        "imghdr",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "json",
        "keyword",
        "kivy",
        "linecache",
        "locale",
        "logging",
        "multiprocessing",
        "ntpath",
        "nturl2path",
        "numbers",
        "opcode",
        "operator",
        "optparse",
        "ujson",
        "os",
        "pathlib",
        "pickle",
        "pkgutil",
        "platform",
        "posixpath",
        "py_compile",
        "pydantic",
        "pyinstaller_heartbeat",
        "queue",
        "random",
        "re",
        "reprlib",
        "resource",
        "runpy",
        "secrets",
        "selectors",
        "shutil",
        "signal",
        "socket",
        "sre_compile",
        "sre_constants",
        "sre_parse",
        "stat",
        "string",
        "stringprep",
        "subprocess",
        "sysconfig",
        "tempfile",
        "threading",
        "token",
        "tokenize",
        "traceback",
        "types",
        "typing",
        "typing_extensions",
        "urllib",
        "uu",
        "uuid",
        "warnings",
        "weakref",
        "xml",
        "zipfile",
    ]

    import_diff = list(set(all_imports) - set(minimum_imports))
    import_diff.sort()
    if len(import_diff):
        print("\n---------")
        print("| Bloat |")
        print("---------")
        for i in import_diff:
            print(i)
        print("---------\n")

    import_diff = list(set(minimum_imports) - set(all_imports))
    import_diff.sort()
    if len(import_diff):
        print("\n-------------")
        print("| Not Found |")
        print("-------------")
        for i in import_diff:
            print(i)
        print("-------------\n")


if __name__ == "__main__":
    heartbeat = start_pyinstaller_heartbeat()
    print_pyinstaller_bloat()
    the_ui = HerePassUI()
    the_ui.run()
    the_ui.clean_up_current_file()
    if heartbeat:
        heartbeat.stop_beating()
