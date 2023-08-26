# weather-app

Ceci est un api Flask qui va permettre de scrapper des données depuis l'API openweather et stocker les données dans une table dans Cassandra puis afficher tout sur localhost:5000
On a tout d'abord un app_weather.py qui va scrapper les données depuis un url qu'on a build. Puis on va parser les données en XML.
Ensuite, on se connecte à cassandra et on crée, dans cassandra, un Keyspace s'il n'existe pas encore et une table si elle n'existe pas encore non plus.
Maintenant, on utilise Flask pour créer une route vers localhost:5000/ 
Cette route va nous rediriger vers un template index.html qui va nous servir d'interface.
Depuis l'index, on peut alors rentrer le nom d'un pays et afficher les informations météo qu'on a scrappé sur ce pays.
Flask va regarder dans cassandra si on a déjà scrapper les données sur ce pays si non, il refait un scraping et affiche.

# Les fichiers :

# app_weather.py 
Fait le scraping, la connexion avec Cassandra, l'insertion des données dans Cassandra et la création des routes pour Flask

# Dockerfile
# requirements.txt
contient les librairies nécessaires 
# templates/index.html 
le templates pour Flask
# docker-compose.yaml

#Commandes à lancer : 

sudo docker-compose up
Si tout va bien, allez à l'adresse : localhost:5000
Sinon : 

sudo docker run --name abdata-cassandra -p 7000:7000 -p 7001:7001 -p 7199:7199 -p 9042:9042 -p 9160:9160 -d cassandra:latest
python3 app_weather.py
Allez à l'adresse : localhost:5000
