# Comparateur de Performances des Joueurs LEC

Outil complet, permettant l'extraction, le stockage ainsi que l'analyse via une application Streamlit permettant de comparer le champions pool / KDA des joueurs de la LEC.


## Déroulement

- WebScrapping pour récupérer les summonner name de chaque joueurs LEC via le site LOLPRO : WebScrapping.py
- Extraction des données via L'API RIOT ( puuid, gameid, gameinfo,..) : main.py
- Stockage des données dans fichier CSV, et base de données postgre pour potentiel utilisation futur : stockage_db.py
- Mise en forme des données et exploitation dans une applciation Streamlit : app.py


## Fonctionnalités

- Comparaison côte à côte de deux joueurs
- Visualisation des KDAs moyens par champion
- Filtrage par équipe et joueur
- Affichage des métriques clés (KDA, Solo Kills)
- Interface intuitive et interactive


## Métriques Disponibles

- KDA (Kill/Death/Assist ratio)
- Solo Kills
- Performances par champion



## 👤 Auteur

- Louube

---



