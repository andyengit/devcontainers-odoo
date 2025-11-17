import argparse
from ast import parse
from audioop import add
from hmac import new
import os
import subprocess
from pathlib import Path
import time
import toml
from collections import defaultdict
from configparser import RawConfigParser


ODOO_VERSION = ["15.0", "16.0", "17.0", "18.0", "19.0"]


def config_oca(addons=[], file="OCA"):
    data = defaultdict()
    if not os.path.exists("./odools.toml"):
        print("No existe odools.toml")
        return False

    try:
        with open("odools.toml", "r") as f:
            data = toml.load(f)
    except Exception as error:
        print("Falla en la lectura: %s" % error)
        return

    if not data.get("config"):
        print("No tiene configuracion")
        return
    config = data["config"]

    def parse_oca_addon(name):
        return "${workspaceFolder}/oca/%s" % name

    if not addons:
        addons = [directory for directory in os.listdir("./oca")]
        addons = [parse_oca_addon(name) for name in addons]

    oca_version = []
    print(list(addons))

    for version in ODOO_VERSION:
        for c in config:
            if version == c["name"]:
                oca_version.append(
                    {
                        "name": f"{version}-{file}",
                        "extends": version,
                        "addons_paths": addons,
                        "diagnostic_filters": [
                            {"paths": ["**/oca*/*"], "path_type": "in"}
                        ],
                    }
                )

    new_config = config

    for oca_v in oca_version:
        index = [
            idx
            for idx, key in enumerate(list(new_config))
            if key["name"] == oca_v["name"]
        ]
        if len(index) == 0:
            new_config.append(oca_v)
            continue

        if len(index) != 1:
            continue

        idx = index[0]
        new_config.pop(idx)
        new_config.insert(idx, oca_v)



    data_to_file = data
    data_to_file["config"] = new_config
    with open("odools.toml", "w") as f:
        toml.dump(data_to_file, f)
    print("Success!")


def config_file(file):
    file_path = "./%s" % file

    if not os.path.exists(file_path):
        print("No existe odool %s" % file)
        return False

    data = {}
    try:
        with open(file_path, "r") as f:
            last_option = False
            for line in f.readlines():
                if line.startswith("["):
                    line_name = line.strip().replace("[", "").replace("]", "")
                    data[line_name] = {}
                    last_option = line_name
                    continue
                if line.startswith(";"):
                    continue

                if line.strip() == "":
                    continue

                key, value = line.strip().split("=")
                data[last_option][key.strip()] = value.strip()
    except Exception as error:
        print("Falla en la lectura: %s" % error)
        return

    if "addons_path" not in data["options"].keys():
        print("No tiene addons_path")
        return

    list_addons = []
    addons_paths = data["options"]["addons_path"].split(",")
    for addon in addons_paths:
        list_addons.append(addon.replace("workspace/", "${workspaceFolder}/"))

    config_oca(addons=list_addons, file=file)

    # try:
    #     with open(file_path, "w") as f:
    #         for key, value in data.items():
    #             f.write("[%s]\n" % key)
    #             for k, v in value.items():
    #                 f.write("%s=%s\n" % (k, v))
    #             f.write("\n")
    # except Exception as error:
    #     print("Falla en la escritura: %s" % error)
    #     return


def run():
    # Crear el parser
    parser = argparse.ArgumentParser(description="Script para odools.")

    subparsers = parser.add_subparsers(dest="action", help="Acciones")
    subparsers.add_parser("run", help="config de oca")

    config_parser = subparsers.add_parser("file", help="Construye Odoo")
    config_parser.add_argument("file", help="Database name")

    args = parser.parse_args()

    # Ejecutar la acción correspondiente
    if args.action == "run":
        config_oca()
    elif args.action == "file":
        config_file(args.file)


if __name__ == "__main__":
    run()
