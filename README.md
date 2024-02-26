# NORAD

Outil de monitoring DSI

L'objectif de ce produit sera de centraliser l'activité du système d'information du groupe : puit de log, monitoring du réseau, monitoring de la charge serveur, etc...


Outil / script d'accès versionné pour une meilleure traçabilité


Il se présentera sous la forme d'un site one page / responsive design
Techno : Python / Django / VueJS + kit HTML à trouver ?


Pour interagir avec cette application, cela se passera sous la forme d'une API.


En dehors de l’application elle-même, La première brique sera donc de mettre à disposition un script python qui permettra d'attaquer cette API selon les différentes use cases, qui sera ensuite implémentée dans les différentes outils


/!\ prévoir un système de copie locale au cas où l'applicatif tombe avec éventuellement un système de rattrapage


Idée d'apps :
- Puit de LOG
- Monitoring du réseau
- Monitoring de la charge serveur
- precisions : statut des watchers
- precisions : recueil des requêtes exécutées
- statut des serveurs mongo (par exemple, serveur de prod tombé dans la nuit du 4 au 5 janvier...)
- statut de web serveur apache2
- récupération des versions precisions
- suivi de l'utilisation de simplerest ?


Détails puit de log :
- Outils
- Fonction
- Type : message / erreur
- Horodatage
- Trace
