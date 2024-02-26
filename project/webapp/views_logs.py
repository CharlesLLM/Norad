from datetime import datetime
from django.shortcuts import render
from bson import ObjectId

from utils_n.norad import (
    connect_to_db,
    access,
    logout
)


"""
Fonction d'affichage des logs
"""
def details_logs(request):
    open_connection, norad = connect_to_db()
    response = logout(request)

    if open_connection:
        if access(request)["connected"]==True:
            files_collection = norad["applications"]
            logs_collection = norad["logs"]

            files = []
            details_logs = []

            # récupération de tous les fichiers sources
            for file in files_collection.find({}):
                file["id"] = file['_id']
                files.append(file)

            # formatage de la date
            for log in logs_collection.find({}):
                log['datetime'] = datetime.strftime(log['datetime'], "%Y-%m-%d %H:%M:%S")
                log['source'] = files_collection.find_one({"_id": ObjectId(log["source"])})["name_app"]
                details_logs.append(log)

            response = render(request, "details_logs.html", {
                "logs": details_logs,
                "files": files,
            })

    return response
