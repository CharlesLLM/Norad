"""
    Biblothèque de fonctions d'envoi de données à l'API Norad
    Dernière modification: 2023-02-15 (TD)
    python3 norad_to_export/norad.py
"""

import requests
import json
# modifier l'import pour compatibilité avec projet precisions
from utils_n.norad import (
    connect_to_db,
    import_configuration
)
import subprocess
from datetime import datetime

with open("../norad.config.json", "r") as json_file:
    config = json.load(json_file)

"""
Fonction qui récupère les logs et qui appelle l'API
"""
def push_log(content):
    # Connexion à la BD Norad
    _, norad = connect_to_db()
    # Représente le log formaté
    log = {"content": content}

    # Récupération de la date
    log["datetime"] = str(datetime.now())[:19]
    log["source"] = str(norad["applications"].find_one(
            {"name_app": "precisions"},
            {"name_app": 0})["_id"]
    )

    # Type de log
    if content[1] == "!":
        log["status"] = "ERROR"

    elif content[1] == ">":
        log["status"] = "INFO"

    else:
        log["status"] = "TRACE"

    # Appel de l'API Norad
    requests.post(
        f"http://{config['ip_address_flask']}:5000/api_push/logs", 
        json = log
    )


"""
Fonction qui récupère les donénes d'utilisation du serveur et qui appelle l'API
"""
def push_data(server_name):
    # Connexion à la BD Norad
    _, norad = connect_to_db()

    # Source des données
    source = str(norad["servers"].find_one(
        {"name_server": server_name},
        {"name_server": 0}
    )["_id"])

    disk_name = import_configuration("disk_name")
    # Listage des commandes bash à exécuter sur le serveur
    commands = [f"> {config['path']}usage_data.txt",
        f"top -b -n 1 | grep 'mongodb\|apache2\|python' >> {config['path']}usage_data.txt",
        f"df -H /dev/{disk_name} >> {config['path']}usage_data.txt",
        f"cat {config['path']}usage_data.txt"
    ]

    # Exécution des commandes
    data = {}
    service_data = []
    disk_data = []
    for command in commands:
        command_output = subprocess.check_output(command, shell=True).decode()
        output_list = command_output.splitlines()

        for line in output_list:
            # S'il y a un résultat, récupération de celui-ci
            if command_output != "":
                line = line.split()
                line_datetime = str(datetime.today())

                # Si le premier élément est un nombre (= s'il s'agit de données de services)
                if line[0].isnumeric():
                    service = line[11]
                    cpu_percent = line[8].replace(",", ".")
                    memory_percent = line[9].replace(",", ".")

                    # Construction des données formatées
                    service_data.append(
                        {
                            "datetime": line_datetime,
                            "service": service,
                            "cpu_percent": cpu_percent,
                            "memory_percent": memory_percent,
                            "source": source
                        }
                    )
                # Si le premier élément est le nom du disque (= s'il s'agit de données de disque)
                elif line[0] == f"/dev/{disk_name}":
                    disk_usage = float(line[4].replace("%", ""))

                    # Construction des données formatées
                    disk_data.append(
                        {
                            "datetime": line_datetime,
                            "disk_percent": disk_usage,
                            "source": source
                        }
                    )

    # Définition des données à insérer en BD
    data["service_data"] = service_data
    data["disk_data"] = disk_data

    # Appel de l'API Norad
    requests.post(
        f"http://{config['ip_address_flask']}:5000/api_monitoring", 
        json = data
    )


"""
Fonction qui récupère les requêtes et appelle l'API
"""
def push_query(text):
    query = {"content": text, "datetime": str(datetime.now())[:19]}
    requests.post (
        "http://127.0.0.1:5000/api_push/queries",
        json = query
    )


if __name__ == "__main__":
    # push_log(" > Test log")
    push_data(import_configuration("server_name"))
    # push_query("Comptage de la campagne")
