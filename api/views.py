"""
    API pour insérer des données depuis des données JSON
    Dernière modification: 2023-02-14 (TP)
"""

from bson import ObjectId
from datetime import datetime
from flask import (
    Flask,
    request,
)
from utils_n.norad import(
    connect_to_db
)


app = Flask(__name__)

"""
Fonction qui insert des logs en BD les données JSON
"""
@app.route("/api_push/<string:collection>", methods = ["POST"])
def push_queries_logs(collection):
    # Récupération des données fournies en JSON
    document = request.get_json()
    _, norad = connect_to_db()

    document["datetime"] = datetime.strptime(document["datetime"], "%Y-%m-%d %H:%M:%S")
    if collection == "logs":
        document["source"] = ObjectId(document["source"])
        norad[collection].insert_one(document)

    elif collection == "queries":
        norad[collection].insert_one(document)

    return "200"


"""
Fonction qui insère les données d'utilisation du serveur en BD
"""
@app.route("/api_monitoring", methods = ["POST"])
def insert_monitoring():
    # Récupération des données fournies en JSON
    data = request.get_json()
    success_service = miss_service = success_disk = miss_disk = 0
    _, norad = connect_to_db()

    nb_data = len(data)
    print(f"Récupération de {nb_data} données de monitoring")

    service_data = data["service_data"]
    disk_data = data["disk_data"]

    # Conversion des champs en fonction de leur type respectifs
    for service_line in service_data:
        service_line["cpu_percent"] = float(service_line["cpu_percent"])
        service_line["memory_percent"] = float(service_line["memory_percent"])
        service_line["source"] = ObjectId(service_line["source"])
        service_line["datetime"] = datetime.strptime(service_line["datetime"][:19], "%Y-%m-%d %H:%M:%S")

    for disk_line in disk_data:
        disk_line["disk_percent"] = float(disk_line["disk_percent"])
        disk_line["source"] = ObjectId(disk_line["source"])
        disk_line["datetime"] = datetime.strptime(disk_line["datetime"][:19], "%Y-%m-%d %H:%M:%S")

    insert_service = [service_data[0]]
    # Pour chaque ligne de données de services :
    for line in service_data[1:]:
        found = False
        for final_line in insert_service:
            # Si dans la liste finale on trouve le même service déjà présent :
            if line["service"] == final_line["service"]:
                # Ajout des données supplémentaires que le service prend
                final_line["cpu_percent"] += line["cpu_percent"]
                final_line["memory_percent"] += line["memory_percent"]
                found = True
        
        # Si le service ne figure pas dans la liste finale, ajout de la ligne dans la liste finale
        if found == False:
            insert_service.append(line)

    for value in insert_service:
        value["cpu_percent"] = round(value["cpu_percent"], 1)
        value["memory_percent"] = round(value["memory_percent"], 1)

    print(f"-> {len(insert_service)} données à insérer dans service_data")
    print(f"-> {len(disk_data)} données à insérer dans disk_data")

    # Insertion des données de services
    for service in insert_service:
        try:
            norad["service_data"].insert_one(service)
            success_service += 1

        except ValueError:
            miss_service += 1

    print(f"Monitoring (services): {success_service} éléments insérés et {miss_service} échecs")

    # Insertion des données de disque
    for disk in disk_data:
        try:
            norad["disk_data"].insert_one(disk)
            success_disk += 1

        except ValueError:
            miss_disk += 1

    print(f"Monitoring (disque): {success_disk} éléments insérés et {miss_disk} échecs")

    return f"{success_service+success_disk} insertions et {miss_service+miss_disk} échecs"
