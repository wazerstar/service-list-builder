import argparse
import ctypes
import os
import sys
import winreg
from collections import deque
from configparser import ConfigParser, SectionProxy
from typing import Any, Deque, Dict, List, Set, Tuple, Union

import win32service
import win32serviceutil

from constants import HIVE, USER_MODE_TYPES


def null_terminator(array: List[str]) -> str:
    return "\\0".join(array)


def read_value(path: str, value_name: str) -> Union[Tuple[Any, int], None]:
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except FileNotFoundError:
        return None


def get_dependencies(service: str, kernel_mode: bool = False) -> Set[str]:
    dependencies: Union[List[str], None] = read_value(f"{HIVE}\\Services\\{service}", "DependOnService")  # type: ignore

    # base case
    if dependencies is None or len(dependencies) == 0:
        return set()

    if not kernel_mode:
        # remove kernel-mode services from dependencies list so we are left with user-mode dependencies only
        for dependecy in dependencies:
            service_type: int = read_value(f"{HIVE}\\Services\\{dependecy}", "Type")  # type: ignore

            if service_type not in USER_MODE_TYPES:
                dependencies.remove(dependecy)

    child_dependencies = {
        child_dependency for dependency in dependencies for child_dependency in get_dependencies(dependency)
    }

    return set(dependencies).union(child_dependencies)


def get_present_services() -> Dict[str, str]:
    # keeps track of service in lowercase (key) and actual service name (value)
    present_services: Dict[str, str] = {}

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"{HIVE}\\Services") as key:
        num_subkeys = winreg.QueryInfoKey(key)[0]

        for i in range(num_subkeys):
            service_name = winreg.EnumKey(key, i)

            # handle (remove) user ID in service name
            if "_" in service_name:
                service_name = service_name.rpartition("_")[0]

            present_services[service_name.lower()] = service_name

    return present_services


def parse_config_list(service_list: SectionProxy, present_services: Dict[str, str]) -> Set[str]:
    return {
        present_services[lower_service]
        for service in service_list
        if (lower_service := service.lower()) in present_services
    }


def main() -> int:
    version = "0.5.3"

    print(
        f"service-list-builder Version {version} - GPLv3\nGitHub - https://github.com/amitxv\nDonate - https://www.buymeacoffee.com/amitxv\n"
    )

    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("error: administrator privileges required")
        return 1

    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    elif __file__:
        os.chdir(os.path.dirname(__file__))

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        metavar="<config>",
        type=str,
        help="path to lists config file",
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

    present_services = get_present_services()

    # load sections from config and handle case insensitive entries
    enabled_services = parse_config_list(config["enabled_services"], present_services)
    service_dump = parse_config_list(config["individual_disabled_services"], present_services)
    rename_binaries = set(binary for binary in config["rename_binaries"] if binary != "")

    # check dependencies
    has_dependency_errors = False

    # required for lowercase comparison
    lower_services_set: Set[str] = {service.lower() for service in enabled_services}

    for service in enabled_services:
        # get a set of the dependencies in lowercase
        dependencies = set(service.lower() for service in get_dependencies(service))

        # check which dependencies are not in the user's list
        # then get the actual name from present_services as it was converted to lowercase to handle case inconsistency in Windows
        missing_dependencies = {
            present_services[dependency] for dependency in dependencies.difference(lower_services_set)
        }

        if len(missing_dependencies) > 0:
            has_dependency_errors = True
            print(f"error: {service} depends on {', '.join(missing_dependencies)}")

    if has_dependency_errors:
        return 1

    if enabled_services:
        # populate service_dump with all user mode services
        for _, service_name in present_services.items():
            service_type: int = read_value(f"{HIVE}\\Services\\{service_name}", "Type")  # type: ignore

            if service_type in USER_MODE_TYPES:
                service_dump.add(service_name)

    if args.disable_running:
        for service in service_dump:
            if not win32serviceutil.QueryServiceStatus(service)[1] == win32service.SERVICE_RUNNING:
                service_dump.remove(service)

    # store contents of batch scripts
    ds_lines: Deque[str] = deque()
    es_lines: Deque[str] = deque()

    for binary in rename_binaries:
        if os.path.exists(binary):
            file_name = os.path.basename(binary)
            file_extension = os.path.splitext(file_name)[1]

            if file_extension == ".exe":
                # processes should be killed before being renamed
                ds_lines.append(f"taskkill /f /im {file_name}")

            last_index = binary[-1]  # .exe gets renamed to .exee
            ds_lines.append(f'REN "{binary}" "{file_name}{last_index}"')
            es_lines.append(f'REN "{binary}{last_index}" "{file_name}"')
        else:
            print(f"info: item does not exist: {binary}")

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"{HIVE}\\Control\\Class") as key:
        num_subkeys = winreg.QueryInfoKey(key)[0]

        for i in range(num_subkeys):
            filter_id = winreg.EnumKey(key, i)

            for filter_type in ("LowerFilters", "UpperFilters"):
                original: Union[List[str], None] = read_value(f"{HIVE}\\Control\\Class\\{filter_id}", filter_type)  # type: ignore

                # check if the filter exists
                if original is not None:
                    new = original.copy()  # to keep a backup of the original
                    for driver in original:
                        if driver in service_dump:
                            new.remove(driver)

                    # check if original was modified at all
                    if original != new:
                        ds_lines.append(
                            f'reg.exe add "HKLM\\%HIVE%\\Control\\Class\\{filter_id}" /v "{filter_type}" /t REG_MULTI_SZ /d "{null_terminator(new)}" /f'
                        )
                        es_lines.append(
                            f'reg.exe add "HKLM\\%HIVE%\\Control\\Class\\{filter_id}" /v "{filter_type}" /t REG_MULTI_SZ /d "{null_terminator(original)}" /f'
                        )

    for service in sorted(service_dump, key=str.lower):
        original_start_value = read_value(f"{HIVE}\\Services\\{service}", "Start")

        if original_start_value is not None:
            ds_lines.append(
                f'reg.exe add "HKLM\\%HIVE%\\Services\\{service}" /v "Start" /t REG_DWORD /d "{original_start_value if service in enabled_services else 4}" /f'
            )

            es_lines.append(
                f'reg.exe add "HKLM\\%HIVE%\\Services\\{service}" /v "Start" /t REG_DWORD /d "{original_start_value}" /f'
            )

    if not ds_lines:
        print("info: there are no changes to write to the scripts")
        return 0

    for array in (ds_lines, es_lines):
        array.appendleft(f'set "HIVE={HIVE}"')
        array.appendleft("@echo off")
        array.append("shutdown /r /f /t 0")

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
