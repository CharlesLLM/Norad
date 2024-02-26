"""
    Bibliothèque de fonctions génériques pour le projet norad
    Dernière modification: 2023-01-31 (TD)
"""

import datetime
import hashlib
import json
from pymongo import MongoClient
from pathlib import Path
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import datetime, timedelta


"""
Fonction de connexion à la base de données
"""
def connect_to_db():
    try:
        uri = import_configuration("mongodb", "uri")
        server = MongoClient(uri)
        norad = server.norad
        return_value = True

    except Exception:
        norad = None
        return_value = False

    return return_value, norad

"""
Fonction qui hash en MD5 ou en SHA256 la string envoyée
"""
def hash(string, algorithm="SHA256"):
    try:
        encoded_string = str.encode(string)
        if algorithm == "MD5":
            md5 = hashlib.md5()
            md5.update(encoded_string)
            return_value = md5.hexdigest()

        else:
            sha256 = hashlib.sha256()
            sha256.update(encoded_string)
            return_value = sha256.hexdigest()

    except Exception as error:
        print(f" ! Une erreur s'est produite durant 'hash': {error} {type(error)}")
        return_value = ""

    return return_value

"""
Fonction qui va récupérer la configuration dans le fichier config.json
"""
def import_configuration(section, key=""):
    absolute_path = Path(__file__).resolve().parent.parent
    try:
        with open(f"{absolute_path}/norad.config.json", "r") as json_file:
            data = json.load(json_file)

        if key != "":
            return_value = data[section][key]

        else:
            return_value = data[section]

    except Exception as error:
        print(f" ! Une erreur s'est produite durant 'import_configuration': {error} {type(error)}")
        return_value = ""

    return return_value

"""
Fonction qui écrit dans les logs
"""
def track(message=""):
    message = message.strip()
    try:
        _, norad = connect_to_db()
        log = {
            "content": message,
            "datetime": datetime.datetime.today().replace(microsecond=0),
            "source": norad["applications"].find_one(
                {"name_app": "norad"},
                {"name_app": 0})["_id"],
        }
        print(message)
        # Définition du statut log suivant le patterne de message
        if message[0] == ">":
            log["status"] = "TRACE"

        elif message[0] == "!":
            log["status"] = "ERROR"

        else:
            log["status"] = "INFO"
        norad["logs"].insert_one(log)
        return_value = True

    except Exception as error:
        print(f" ! Une erreur s'est produite durant 'track': {error} {type(error)}")
        return_value = False

    return return_value


if __name__ == "__main__":
    print(track(" Test info du tracking"))
    print(track(" ! Test erreur du tracking"))
    print(track(" > Test trace du tracking"))

"""
Fonction qui récupère le cookie de connexion et renvoie son état
"""
def access(request):
    user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if user_ip_address:
        ip = user_ip_address.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    if import_configuration("wl", "local") == hash(ip):
        return {"connected": True}

    connected_token = request.COOKIES.get("connected_token")

    if connected_token is not None:
        connected_token = connected_token.replace("-", "/")[0:19]
        connected_at = connected_token[8:10] + "/" + connected_token[5:8] + connected_token[0:4] +\
            connected_token[10:]
        connected_at = datetime.strptime(connected_at, "%d/%m/%Y %H:%M:%S")

        disconnected_at = connected_at + timedelta(minutes=10)
        now = datetime.now()

        if now < disconnected_at:
            return {"connected": True, "connected_at": connected_at}

    return {"connected": False}

"""
Fonction qui supprime le cokkie de connexion
"""
def logout(request):
    response = HttpResponseRedirect(
        reverse(
            "connection"
        )
    )
    response.delete_cookie("connected_token")

    return response