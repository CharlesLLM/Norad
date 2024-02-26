from datetime import datetime, timedelta
from django.shortcuts import render
from bson.objectid import ObjectId
from utils_n.norad import (
    connect_to_db,
    access,
    logout
)


"""
Fonction qui récupère les données de monitoring de tous les serveurs
"""
def monitoring(request):

    # Connexion à la BDD norad
    open_connection, norad = connect_to_db()
    response = logout(request)

    if open_connection:
        if access(request)["connected"] == True:
            servers_collection = norad["servers"]

            # used_servers = {}
            servers_list = []
            data = {}
            for server in servers_collection.find():
                server_id = server["_id"]
                server_name = server["name_server"]

                # Récupération de la dernière liste de données inscrite en BD pour chaque serveur
                parameters = {
                    "source": server_id,
                    "from": datetime.today() - timedelta(days=1),
                    "to": datetime.today(),
                    "sort": True
                }
                values = get_values(norad, parameters)

                if values is not None:
                    server_data = values.copy()
                    server_data.reverse()
                    server_data = server_data[:3]

                    for line in server_data:
                        line_date = line["datetime"].strftime("%d/%m/%Y")
                        line_hour = line["datetime"].strftime("%H:%M:%S")
                        if line_date < datetime.now().strftime("%d/%m/%Y"):
                            line["datetime"] = "Hier: " + line_hour
                        else:
                            line["datetime"] = "Aujourd'hui: " + line_hour
                    
                    data[server_name] = server_data
                else:
                    data[server_name] = []

                servers_list.append(server_name)

            context = {}
            context["data"] = data
            context["servers"] = servers_list

            return render(request, "monitoring.html", context)

    return response

"""
Fonction qui récupère les données de monitoring du serveur dont l'id est passé en paramètre
"""
def monitoring_server(request, name_server):

    # Connexion à la BDD norad
    open_connection, norad = connect_to_db()
    response = logout(request)

    if open_connection:
        if access(request)["connected"] == True:

            # Nom du serveur concerné
            id_server = norad["servers"].find_one({ "name_server": name_server })["_id"]

            context = {}
            context["name"] = name_server
            context["source"] = id_server

            # 1e graphique : 24 dernières heures, et pics toutes les heures (via le cron)
            list_day = day_chart_data(norad, id_server)
            context["day_chart_values"] = list_day

            # 2e graphique : Dernière semaine, et max de toutes les 4h
            list_week = week_chart_data(norad, id_server)
            context["week_chart_values"] = list_week

            # Liste des chutes de services
            list_drops = week_drops(norad, id_server)
            context["drops"] = list_drops

            # Détails : Récupère toutes les données de la dernière semaine
            values_parameters = {
                "source": ObjectId(id_server),
                "from": datetime.today() - timedelta(days=7),
                "to": datetime.today(),
                "sort": True
            }
            details = get_values(norad, values_parameters)
            try:
                details.reverse()

            except:
                pass

            context["details"] = details

            response = render(request, "server_monitoring.html", context)

            # Gestion du cookie
            timer_token = request.COOKIES.get("timer_token")
            if timer_token is None:
                response.set_cookie(key="timer_token", value=10000, path="/monitoring")

    return response

"""
Fonction qui récupère les données de monitoring du serveur dont l'id est passé en paramètre pour les
dernières 24h
"""
def day_chart_data(norad, source):

    today = datetime.today()
    yesterday = today - timedelta(days=1)
    values_parameters = {
        "source": ObjectId(source),
        "from": yesterday,
        "to": today,
        "sort": True
    }
    day_values = get_values(norad, values_parameters)

    if day_values is not None:
        # Conversion des dates en string lisibles pour le graphique
        for value in day_values:
            value_date = value["datetime"].strftime("%d/%m/%Y")
            value_hour = value["datetime"].strftime("%H:%M")
            if value_date < datetime.now().strftime("%d/%m/%Y"):
                value["datetime"] = "Hier " + value_hour
            else:
                value["datetime"] = "Aujourd\'hui " + value_hour

        return day_values
    
    return None

"""
Fonction qui récupère les données de monitoring du serveur dont l'id est passé en paramètre pour les
7 derniers jours
"""
def week_chart_data(norad, source):

    today = datetime.today()
    one_week_ago = today - timedelta(days=7)
    values_parameters = {
        "source": ObjectId(source),
        "from": one_week_ago,
        "to": today,
        "sort": True
    }
    week_values = get_values(norad, values_parameters)

    if week_values is not None:

        list_week = []
        gap = one_week_ago

        # Pour chaque intervalle de 4h :
        while gap < today:
            cpu_values = []
            memory_values = []
            disk_values = []
            for sort_line in week_values:
                # Si la donnée lue est comprise dans l'intervalle, ajout de chaque donnée dans une 
                # liste pour ensuite calculer le maximum du composant sur l'intervalle
                if (sort_line["datetime"] > gap and 
                    sort_line["datetime"] < gap + timedelta(hours=4)):
                    cpu_values.append(sort_line["cpu_percent"])
                    memory_values.append(sort_line["memory_percent"])
                    disk_values.append(sort_line["disk_percent"])

            # Calcul des maximums
            if cpu_values:
                cpu_max = max(cpu_values)
                memory_max = max(memory_values)
                disk_max = max(disk_values)

                # Définition des données pour l'intervalle
                gap_value = {
                    "datetime": gap + timedelta(hours=4),
                    "cpu_percent": cpu_max,
                    "memory_percent": memory_max,
                    "disk_percent": disk_max,
                }
            else:
                gap_value = {
                    "datetime": gap + timedelta(hours=4),
                    "cpu_percent": 0,
                    "memory_percent": 0,
                    "disk_percent": 0,
                }
            list_week.append(gap_value)

            # Passage au prochain intervalle de 4h
            gap = gap + timedelta(hours=4)
        
        # Conversion des dates en string lisibles pour le graphique
        for value in list_week:
            value["datetime"] = value["datetime"].strftime("%d/%m %H:%M")

        return list_week
    
    return None

"""
Fonction qui utilise les données de service_data pour trouver les instants auxquels certains
services sont tombés
"""
def week_drops(norad, source):
    # Ajouter apache2 quand l'application sera mise en ligne
    services_list = ["mongod", "python3"]

    today = datetime.today()
    one_week_ago = datetime.today() - timedelta(days=7)
    values_parameters = {
        "source": ObjectId(source),
        "from": one_week_ago,
        "to": today,
        "sort": False
    }
    services_values = get_values(norad, values_parameters)

    if services_values is not None:
        list_drops = []
        gap = one_week_ago

        # Pour chaque intervalle de 4h :
        while gap < today:
            gap_values = []
            for sort_line in services_values:
                # Si la donnée lue est comprise dans l'intervalle, ajout de la ligne dans une liste
                # pour ensuite vérifier s'il ne manque pas de service
                if (sort_line["datetime"] > gap and 
                    sort_line["datetime"] < gap + timedelta(minutes=5)):
                    gap_values.append(sort_line)

            if len(gap_values) > 0:
                # Pour chaque service
                for service in services_list:
                    service_exists = False
                    # Pour chaque ligne de données
                    for gap_value in gap_values:
                        if service == gap_value["service"]:
                            service_exists = True

                    # Si le service n'est pas trouvé à un instant
                    if service_exists == False:
                        # On fait défiler la liste des drops déjà répertoriés
                        if len(list_drops) == 0:
                            drop = {
                                "begin_drop": gap.strftime("%d/%m %H:%M"),
                                "end_drop": (gap + timedelta(minutes=5)).strftime("%d/%m %H:%M"),
                                "service": service
                            }
                            list_drops.append(drop)
                        else:
                            drop_already_exists = False
                            for drop_value in list_drops:
                                # Si on y trouve un drop du même service 5 minutes plus tôt
                                if drop_value["service"] == service and drop_value["end_drop"] == gap.strftime("%d/%m %H:%M"):
                                    # On rajoute 5 minutes au délai du drop
                                    drop_value["end_drop"] = (gap + timedelta(minutes=5)).strftime("%H:%M")
                                    drop_already_exists = True
                                else:
                                    # Sinon on crée le drop
                                    drop = {
                                        "begin_drop": gap.strftime("%d/%m %H:%M"),
                                        "end_drop": (gap + timedelta(minutes=5)).strftime("%H:%M"),
                                        "service": service
                                    }

                            if drop_already_exists == False:
                                list_drops.append(drop)

            # Passage au prochain intervalle de 4h
            gap = gap + timedelta(minutes=5)
        
        return list_drops

"""
Fonction qui va récupérer des données de monitoring entre 2 variables datetime passées en paramètres
et faire une unique liste d'objets avec toutes les données à l'intérieur
"""
def get_values(norad, parameters):
    
    service_collection = norad["service_data"]
    disk_collection = norad["disk_data"]
    query_parameters = {
        "datetime": {
            "$gt": parameters["from"],
            "$lte": parameters["to"]
        }
    }
    if "source" in parameters:
        query_parameters["source"] = parameters["source"]
    service_values = list(service_collection.find(query_parameters).sort("datetime"))
    disk_values = list(disk_collection.find(query_parameters).sort("datetime"))

    if (len(service_values) > 0) and (len(disk_values) > 0):
        if parameters["sort"] == True:
            # Concaténation des donées du même moment
            service_values = sort_data(service_values)

        # Définition des données finales
        final_values =  service_values.copy()
        # Ajout des données de disque aux données de service
        for final_value in final_values:
            final_value["id"] = final_value["_id"]
            for disk_value in disk_values:
                if final_value["datetime"] == disk_value["datetime"]:
                    final_value["disk_percent"] = round(disk_value["disk_percent"], 1)

            return final_values
        
        return service_values

"""
Fonction qui va additionner les ressources utilisées par chaque service si elles sont utilisées au
même moment
"""
def sort_data(raw_list):
    sorted_list = [raw_list[0]]
    # On additionne toutes les ressources prises à chaque instant
    for line in raw_list[1:]:
        exists = False
        for value in sorted_list:
            if line["datetime"] == value["datetime"]:
                value["cpu_percent"] += line["cpu_percent"]
                value["memory_percent"] += line["memory_percent"]
                exists = True
                # Suppression du service (données concaténées)
                # del value["service"]
            value["memory_percent"] = round(value["memory_percent"], 1)
        
        # Si le service ne figure pas dans la liste finale, ajout de la ligne dans la liste finale
        if exists == False:
            sorted_list.append(line)
    
    return sorted_list
