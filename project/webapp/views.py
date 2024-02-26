from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from bson import ObjectId
from webapp import forms
from datetime import datetime, timedelta
from utils_n.norad import (
    import_configuration,
    hash,
    connect_to_db,
    access,
    logout
)
from .views_monitoring import get_values


"""
Fonction de connexion pour l'utilisateur
"""
def connection(request):
    # recupération de l'ip utilisateur
    user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if user_ip_address:
        ip = user_ip_address.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    response = render(request, "login.html")

    # récupération et formatage du cookie

    # si l'utilisateur n'est pas white list retourner le formulaire de connexion
    # modifier le norad.config.json -> wl.local => effacer "<retirer>"    
    if hash(ip) != import_configuration("wl", "local"):
        # si le cookie de connexion est valide
        if access(request)["connected"] == True:
            response = HttpResponseRedirect(reverse("dashboard"))

        else:
            # après validation du formulaire de connexion
            if request.method == "POST":
                # vérification des données saisies
                form = forms.form_login(request.POST)
                if form.is_valid():
                    # Récupération de l'utilisateur en base
                    password = form.cleaned_data["password"]

                    open_connection, norad = connect_to_db()
                    if open_connection:
                        predicate = {"password": hash(password)}
                        user = norad.connection.find_one(predicate)

                        # Si l'utilisateur existe
                        if user is not None:
                            update = {"$set": {"lastconnection": datetime.now()}}
                            norad.connection.update_one({}, update)

                            response = HttpResponseRedirect(reverse("dashboard"))
                            response.set_cookie("connected_token", str(datetime.now()))

                        else:
                            response = render(request, 'login.html', {
                                "error": "Mot de passe incorrect"
                            })
                    
                    else:
                        response = render(request, "login.html", {
                            "error": "Erreur de connexion à la base de données"
                        })
                else:
                    response = render(request, "login.html", {
                        "error": "Le formulaire n'est pas remplie"
                    })

    else:
        response = HttpResponseRedirect(reverse("dashboard"))
        response.set_cookie("connected", "admin_access", 2147483647)

    return response


"""
Fonction qui renvoie le dashbaord
"""
def dashboard(request):
    response = logout(request)
    if access(request)["connected"] == True:
        data = {"last_logs": [], "last_usage": [], "last_queries": []}
        _, norad = connect_to_db()

        # Récupére les 3 derniers logs précisions insérés en BD
        source_log = norad["applications"].find_one({"name_app": "precisions"})
        list_logs = norad["logs"].find(
            {"source": ObjectId(source_log["_id"])}).sort("datetime", -1).limit(5)

        # Formatage de la date et récupération du nom des sources
        for log in list_logs:
            log["datetime"] = datetime.strftime(log["datetime"], "%Y-%m-%d %H:%M:%S")
            log["source"] = source_log["name_app"].upper()
            data["last_logs"].append(log)

        # Récupére les 3 derniers relevés des ressources insérés en BD
        source_usage = norad["servers"].find_one({"name_server": "precisions-preprod"})["_id"]
        usage_parameters = {
            "source": source_usage,
            "from": datetime.today() - timedelta(days=1),
            "to": datetime.today()
        }
        usages = get_values(norad, usage_parameters)
        
        if usages:
            usages.reverse()
            # Formatage de la date et récupération du nom des sources
            for usage in usages:
                usage["datetime"] = datetime.strftime(usage["datetime"], "%Y-%m-%d %H:%M:%S")
                usage["source"] = source_log["name_app"].upper()
                if len(data["last_usage"]) < 5:
                    data["last_usage"].append(usage)

        # Récupére les 3 dernières requêtes precisions insérées en BD
        queries = norad["queries"].find().sort("datetime", -1).limit(5)
        # Formatage de la date
        for querie in queries:
            querie["datetime"] = datetime.strftime(querie["datetime"], "%Y-%m-%d %H:%M:%S")
            data["last_queries"].append(querie)
        
        response = render(request, "dashboard.html", {
            "data": data,
        })

    return response


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