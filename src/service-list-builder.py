import argparse
import ctypes
import os
import sys
import winreg
from configparser import ConfigParser
from typing import Any, List, Tuple, Union

import pywintypes
import win32con
import win32service
import win32serviceutil


def split_lines(array: List[str]) -> str:
    return "\\0".join(array)


def read_value(path: str, value_name: str) -> Union[Tuple[Any, int], None]:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except FileNotFoundError:
        return None


def main() -> int:
    version = "0.4.1"

    filter_dict = {
        "{4d36e967-e325-11ce-bfc1-08002be10318}": {"LowerFilters"},
        "{71a27cdd-812a-11d0-bec7-08002be2092f}": {"LowerFilters", "UpperFilters"},
        "{4d36e96c-e325-11ce-bfc1-08002be10318}": {"UpperFilters"},
        "{6bdd1fc6-810f-11d0-bec7-08002be2092f}": {"UpperFilters"},
        "{ca3e7ab9-b4c3-4ae6-8251-579ef933890f}": {"UpperFilters"},
    }

    class_hive = "SYSTEM\\CurrentControlSet\\Control\\Class"
    services_hive = "SYSTEM\\CurrentControlSet\\Services"

    print(f"service-list-builder Version {version}\nCopyright (C) github.com/amitxv. All rights reserved.\n")

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("error: administrator privileges required")
        return 1

    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    elif __file__:
        os.chdir(os.path.dirname(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        metavar="<config>",
        type=str,
        help="path to lists config file",
        required=True,
    )
    parser.add_argument(
        "--disable_running",
        help="only disable services specified in the list that are currently running",
        action="store_true",
    )
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print("error: config file not found")
        return 1

    config = ConfigParser(allow_no_value=True, delimiters=("="), inline_comment_prefixes="#")
    # prevent lists imported as lowercase
    config.optionxform = str  # type: ignore
    config.read(args.config)

    automatic = set(service for service in config["automatic"] if service)
    manual = set(service for service in config["manual"] if service)
    service_dump = set(driver for driver in config["disable_drivers"] if driver)
    rename_binaries = set(binary for binary in config["rename_binaries"] if binary)

    statuses = win32service.EnumServicesStatus(win32service.OpenSCManager(None, None, win32con.GENERIC_READ))

    if automatic or manual:
        service_name: str
        for service_name, _, _ in statuses:  # TODO: populate list manually by looping through keys
            # remove _XXXXX user services id
            if "_" in service_name:
                service_name = service_name.rpartition("_")[0]

            service_dump.add(service_name)

    service_dump = sorted(service_dump, key=str.lower)

    if args.disable_running:
        for service in service_dump:
            try:
                if not win32serviceutil.QueryServiceStatus(service)[1] == win32service.SERVICE_RUNNING:
                    service_dump.remove(service)
            except pywintypes.error as e:
                # ignore if service does not exist
                if e.args[0] == 1060:
                    pass

    # store contents of batch scripts
    ds_lines: List[str] = []
    es_lines: List[str] = []

    ds_lines.append("@echo off")
    es_lines.append("@echo off")

    for binary in rename_binaries:
        if os.path.exists(binary):
            file_name: str = os.path.basename(binary)
            last_index = binary[-1]  # .exe gets renamed to .exee
            ds_lines.append(f'REN "{binary}" "{file_name}{last_index}"')
            es_lines.append(f'REN "{binary}{last_index}" "{file_name}"')
        else:
            # TODO: ask user if they want to disable it anyway and argument to supress all choices
            print(f"info: item does not exist: {binary}")

    for filter_id, filter_types in filter_dict.items():  # TODO: loop through keys instead of hardcoding them
        for filter_type in filter_types:
            original: Union[List[str], None] = read_value(f"{class_hive}\\{filter_id}", filter_type)  # type: ignore

            # check if the filter exists
            if original is not None:
                new = original.copy()  # to keep a backup of the original
                for driver in original:
                    if driver in service_dump:
                        new.remove(driver)

                # check if original was modified at all
                if original != new:
                    ds_lines.append(
                        f'reg.exe add "HKLM\\{class_hive}\\{filter_id}" /v "{filter_type}" /t REG_MULTI_SZ /d "{split_lines(new)}" /f'
                    )
                    es_lines.append(
                        f'reg.exe add "HKLM\\{class_hive}\\{filter_id}" /v "{filter_type}" /t REG_MULTI_SZ /d "{split_lines(original)}" /f'
                    )

    for service in service_dump:
        original_start_value = read_value(f"{services_hive}\\{service}", "Start")

        if original_start_value is not None:
            if service in automatic:
                new_start_value = 2
            elif service in manual:
                new_start_value = 3
            else:
                new_start_value = 4

            ds_lines.append(
                f'reg.exe add "HKLM\\{services_hive}\\{service}" /v "Start" /t REG_DWORD /d "{new_start_value}" /f'
            )

            es_lines.append(
                f'reg.exe add "HKLM\\{services_hive}\\{service}" /v "Start" /t REG_DWORD /d "{original_start_value}" /f'
            )

    ds_lines.append("shutdown /r /f /t 0")
    es_lines.append("shutdown /r /f /t 0")

    if len(ds_lines) == 2:
        print("info: there are no changes to write to the scripts")
        return 0

    os.makedirs("build", exist_ok=True)

    with open("build\\Services-Disable.bat", "w", encoding="utf-8") as file:
        for line in ds_lines:
            file.write(f"{line}\n")

    with open("build\\Services-Enable.bat", "w", encoding="utf-8") as file:
        for line in es_lines:
            file.write(f"{line}\n")

    print("info: done")

    return 0


if __name__ == "__main__":
    sys.exit(main())
