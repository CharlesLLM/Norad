"""
    Script d'initialisation de la base de données
    Dernière modification: 2023-01-31 (TD)
    python3 10_general_base.py
"""

from utils_n.norad import (
    hash,
    import_configuration,
    track
)
from os import path
from pymongo import MongoClient
import datetime


# Connexion au server MongoDB
server = MongoClient(import_configuration("mongodb", "uri"))
database = server["norad"]

# Suppression de la base de données existante
server.drop_database("norad")

# Création du mot de passe
connection = database["connection"]
connection.drop()
record = {
    "password": hash("Norad_" + str(datetime.date.today())),
    "lastconnection": None,
    "datemodification": datetime.datetime.today().replace(microsecond=0),
}
connection.insert_one(record)

# Chargement des applications
apps = database["applications"]
apps.drop()
file  = "data/applications.txt"
if path.isfile(file):
    with open(file, "r", encoding="latin") as referencial:
        read = 0
        written = 0
        for line in referencial:
            read += 1
            record = {
                "name_app": line.replace("\n", ""),
            }
            apps.insert_one(record)
            written += 1
    apps_log = f" > {written} documents insérés sur {read} lus"

else:
    apps_log = " ! Référentiel applications non trouvé"
    track(" ! Référentiel applications non trouvé")

# Initialisation de la collection logs
logs = database["logs"]
logs.drop()

# Insertion des logs de cette initialisation
track("Initilisation de la base données")
track(" > Chargement des applications")
track(apps_log)

# Chargement des serveurs
track(" > Chargement des serveurs")
servers = database["servers"]
servers.drop()
file  = "data/servers.txt"
if path.isfile(file):
    with open(file, "r", encoding="latin") as referencial:
        read = 0
        written = 0
        for line in referencial:
            read += 1
            cut = line.split("\t")
            record = {
                "name_server": cut[0].strip(),
            }
            servers.insert_one(record)
            written += 1
    servers_data = f" > {written} documents insérés sur {read} lus"

else:
    track(" ! Référentiel servers non trouvé")
    servers_data = " ! Référentiel servers non trouvé"

# Initialisation de la collection usage_data
service_data = database["service_data"]
service_data.drop()

# Initialisation de la collection disk_data
disk_data = database["disk_data"]
disk_data.drop()

# Insertion des logs de cette initialisation
track("Initilisation de la base données")
track(" > Chargement des servers")
track(servers_data)
