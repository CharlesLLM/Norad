from datetime import datetime
from django.shortcuts import render

from utils_n.norad import (
    connect_to_db
)
from .views import (
    access,
    logout
)

"""
Fonction d'affichage de la page des requêtes precisions
"""
def queries(request):
    open_connection, norad = connect_to_db()
    response = logout(request)

    if open_connection:
        if access(request)["connected"]==True:

            queries = []

            # formatage de la date
            for query in norad["queries"].find({}).sort("datetime", -1):
                query['datetime'] = datetime.strftime(query['datetime'], "%Y-%m-%d %H:%M:%S")
                queries.append(query)

            response = render(request, "queries.html", {
                "queries": queries,
            })

    return response