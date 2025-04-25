
import json,time,os,requests,csv
import psycopg2
from tqdm import tqdm

class BaseAPI:
    """
    Classe de base pour gérer les fonctionnalités génériques des requêtes API.
    Inclut la gestion des clés API, des en-têtes, et des limitations.
    """
    
    def __init__(self, api_key_path):
        """
        Initialise avec une clé API et configure les headers.
        :param api_key_path: Chemin vers le fichier contenant la clé API.
        """
        self.api_key = self._load_api_key(api_key_path)
        self.headers = {
            'X-Riot-Token': self.api_key
        }

    def _load_api_key(self, path):
        """
        Charge la clé API à partir d'un fichier JSON.
        :param path: Chemin vers le fichier JSON contenant la clé API.
        :return: La clé API sous forme de chaîne.
        """
        with open(path, "r") as keys_file:
            return json.load(keys_file)['api_key']

    def make_request_max_limit(self, url, params=None, max_retries=5):
        """
        Réalise une requête GET en gérant les limitations de l'API (par ex. code 429).
        
        :param url: URL de l'API cible.
        :param params: Paramètres optionnels pour la requête.
        :param max_retries: Nombre maximum de réessais autorisés.
        :return: La réponse de la requête HTTP en format JSON.
        """
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                print(f"Statut HTTP reçu: {response.status_code}")
                return response.json()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:  # Si on dépasse les limites
                    wait_time = int(response.headers.get("Retry-After", 1))
                    print(f"Limite atteinte. Pause de {wait_time} secondes...")
                    for _ in tqdm(range(wait_time), desc="Attente . . .", unit="s"):
                        time.sleep(1)
                    retries += 1
                else:
                    raise e
            except requests.exceptions.RequestException as e:
                print(f"Erreur réseau : {e}. Nouvelle tentative dans 1 seconde...")
                time.sleep(1)
                retries += 1
        raise Exception("Nombre max de tentatives atteint.")

class DBManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname="db_lol",
                user="postgres",
                password="root",
                host="localhost"
            )
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
            raise

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def insert_rows(self, table_name, statsdujoueur):
        # Liste complète des colonnes
        columns = [
            "gameid", "player", "team", "game_number", "game_version", "teamid", "lane", "poste", 
            "champion", "kills", "deaths", "assists", "kda", "champlevel", "win", 
            "item0", "item1", "item2", "item3", "item4", "item5", "item6", 
            "gold_earn", "totaldmgdealtochamp", "totaldmgtaken", "totalheal", "longesttimealive", 
            "ennemy_cc", "cs_kill", "jungle_minions_kills", "minions_kill", "visionscore", 
            "visionwardsboughtingame", "wardsplaced", "wardskilled", "detectorwardsplaced", 
            "timeplayed", "branch1", "branch2", "perk0", "perk1", "perk2", "perk3", 
            "perk4", "perk5", "defense", "flex", "offense", "summoner1id", "summoner2id", 
            "ban_1_ally", "ban_2_ally", "ban_3_ally", "ban_4_ally", "ban_5_ally", 
            "ban_1_ennemy", "ban_2_ennemy", "ban_3_ennemy", "ban_4_ennemy", "ban_5_ennemy", 
            "nb_kill_team", "first_blood", "nb_drake_team", "first_drake", 
            "nb_herald_team", "first_herald", "nb_baron_team", "first_baron", 
            "nb_inib_team", "first_inib", "nb_tower_team", "first_tower", 
            "nb_kill_oposing_team", "nb_drake_oposing_team", "nb_herald_oposing_team", 
            "nb_baron_oposing_team", "nb_inib_oposing_team", "nb_tower_oposing_team", 
            "skillshotsdodged", "quickcleanse", "solokills", "laneminionsfirst10minutes", 
            "goldperminute", "gamelength"
        ]
        
        # Construction de la requête dynamique
        columns_joined = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        
        query = f"""INSERT INTO {table_name} ({columns_joined}) 
                    VALUES ({placeholders}) 
                    ON CONFLICT DO NOTHING"""
        print(f"Number of columns: {len(columns)}")
        print(f"Number of elements in statsdujoueur: {len(statsdujoueur)}")
        print(statsdujoueur)

        try:
            # Utilisation du gestionnaire de contexte pour le curseur
            with self.conn.cursor() as cur:
                # Exécution de la requête
                cur.execute(query, statsdujoueur)
                # Validation des changements
                self.conn.commit()
        except psycopg2.Error as e:
            # Gestion des erreurs et rollback en cas de problème
            print(f"Error running query: {e}")
            self.conn.rollback()


    
    # Classe spécialisée pour Riot API
class RIOTAPI(BaseAPI,DBManager):
    """
    Classe pour encapsuler les fonctionnalités spécifiques à l'API de Riot.
    Hérite de BaseAPI pour ses fonctionnalités de base.
    """
    def __init__(self, api_key_path):
        # Appelle d'abord le constructeur de DBManager
        DBManager.__init__(self)

        # Appelle ensuite le constructeur de BaseAPI avec l'argument requis
        BaseAPI.__init__(self, api_key_path)

        # Vous pouvez ajouter des attributs spécifiques à RIOTAPI ici
        self.api_key_path = api_key_path

    def get_puuid(self, game_name, tag_line):
        """
        Récupère le PUUID d'un joueur à partir de son GameName et TagLine.
        :param game_name: Nom d'invocateur Riot.
        :param tag_line: Etiquette du joueur (ex. EUW).
        :return: Le PUUID du joueur.
        """
        url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        response = self.make_request_max_limit(url)
        return response.get("puuid")

    def get_match_list(self, puuid, count=100):
        """
        Récupère une liste de matchs pour un joueur donné.
        :param puuid: Identifiant unique du joueur.
        :param count: Nombre maximal de matchs à récupérer (défaut : 100).
        :return: Liste d'identifiants de matchs.
        """
        url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {'type': 'ranked', 'start': 0, 'count': count}
        return self.make_request_max_limit(url, params=params)

    def get_timeline(self, match_id):
        """
        Récupère la timeline d'un match donné.
        :param match_id: Identifiant unique du match.
        :return: Données relatives à la timeline du match.
        """
        url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        return self.make_request_max_limit(url)

    def get_match_data(self, match_id):
        """
        Récupère les données complètes d'un match spécifique.
        :param match_id: Identifiant unique du match.
        :return: Les détails du match.
        """
        url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return self.make_request_max_limit(url)

    def get_data(self,Player,Team,puuid,listefinale):
        statsdujoueurfinale2 = [['Gameid','Player','Team','Game number','Game Version','TeamId','Lane','Poste','Champion','Kills','Deaths','Assists','KDA','ChampLevel','Win','item0','item1','item2','item3','item4','item5','item6','Gold Earn','TotalDmgDealtoChamp','TotalDmgTaken','TotalHeal','LongestTimeAlive','Ennemy_CC','CS Kill','Jungle Minions Kills','Minions Kill','visionScore','visionWardsBoughtInGame','wardsplaced','wardskilled','detectorWardsPlaced','timePlayed','Branch1','Branch2','perk0','perk1','perk2','perk3','perk4','perk5','defense','flex','offense','summoner1Id','summoner2Id','Ban 1 ally','Ban 2 ally','Ban 3 ally','Ban 4 ally','Ban 5 ally','Ban 1 ennemy','Ban 2 ennemy','Ban 3 ennemy','Ban 4 ennemy','Ban 5 ennemy','Nb Kill Team','First blood','Nb Drake Team','First Drake','Nb Herald Team','First Herald','Nb Baron Team','First Baron','Nb Inib Team','First Inib','Nb Tower Team','First Tower','Nb Kill oposing Team','Nb drake Oposing Team','Nb Herald Oposing team','Nb Baron oposing team','Nb Inib Oposing team','Nb Tower Oposing Team','skillshotsDodged','quickCleanse','soloKills','laneMinionsFirst10Minutes','goldPerMinute','gameLength']]

    
    #Lancement de la boucle pour parser tout les match du joueur en question


        for i in range(len(listefinale)):
        
            Gameid=listefinale[i]
            # 0.6*100 = 60 secondes : 100 requetes max par minute.
            
            #Création de l'url
            url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{str(listefinale[i])}"
            response = self.make_request_max_limit(url)

            if not listefinale or response["info"]["gameDuration"] < 200 or response["info"]["gameMode"]!='CLASSIC':
                break

            #Création de la boucle allant de 1 à 10 pour parser tout les joueur de la game et obtenir le bon joueur
            for l in range(10):
                puuidplayer = response['info']['participants'][l]['puuid']#Test puuid
                #!!!! Supprimer le temps d'attente  !!!!
                #Condition pour être sur d'obteir les data du bon joueur
                if puuidplayer == puuid:
                    print("Game N°",i+1)
                    print(listefinale[i]) 
                    numerojoueur = response['info']['participants'][l]['participantId']-1
                    
                    joueur=response['info']['participants'][numerojoueur]
                    participantid = joueur['participantId']-1
                    
                    # #Information de base sur la game 
                    gameVersion = response['info']['gameVersion']
                    gameMode = response['info']['gameMode']

                    #Stats du joueur choisi 

                    if participantid == numerojoueur:
                        teamId = joueur['teamId']
                        lane = joueur['lane']
                        poste = joueur['individualPosition']
                        championName = joueur['championName']
                        skillshotsDodged=joueur["challenges"]["skillshotsDodged"]
                        quickCleanse=joueur["challenges"]["quickCleanse"]
                        soloKills=joueur["challenges"]["soloKills"]
                        laneMinionsFirst10Minutes=joueur["challenges"]["laneMinionsFirst10Minutes"]
                        goldPerMinute=joueur["challenges"]["goldPerMinute"]
                        gameLength=joueur["challenges"]["gameLength"]

                        kills = joueur['kills']
                        deaths = joueur['deaths']
                        assists = joueur['assists']
                        if deaths >0:
                            KDA = round((joueur['kills'] + joueur['assists'])/joueur['deaths'],2)
                        else:
                            KDA = round((joueur['kills'] + joueur['assists']),2)
                        champLevel =  joueur['champLevel']
                        win = joueur['win']

                        #Gold
                        item0 = joueur['item0']
                        item1 = joueur['item1']
                        item2 = joueur['item2']
                        item3 = joueur['item3']
                        item4 = joueur['item4']
                        item5 = joueur['item5']
                        item6 = joueur['item6']
                        goldEarned = joueur['goldEarned']

                        #STATS du joueur :
                        
                        #Graph
                        totalDamageDealtToChampions = joueur['totalDamageDealtToChampions']
                        totalDamageTaken = joueur['totalDamageTaken']
                        totalHeal = joueur['totalHeal'] 
                        longestTimeSpentLiving = joueur['longestTimeSpentLiving']
                        timeCCingOthers = joueur['timeCCingOthers']

                        #CSing
                        CreepKill =  joueur['totalMinionsKilled']
                        junglemobkill = joueur['neutralMinionsKilled']
                        totalMinionsKill = joueur['totalMinionsKilled'] + joueur['neutralMinionsKilled']
                    

                        #Vision

                        visionScore = joueur['visionScore'] 
                        visionWardsBoughtInGame =  joueur['visionWardsBoughtInGame']
                        wardsplaced = joueur['wardsPlaced']
                        wardskilled = joueur['wardsKilled']
                        detectorWardsPlaced = joueur['detectorWardsPlaced']


                        timePlayed = joueur['timePlayed']/60

                        #RUNES 

                        #Branche de rune
                        Branch1 = joueur['perks']['styles'][0]['style']
                        Branch2 = joueur['perks']['styles'][1]['style']

                        #Primaire
                        perk0 = joueur['perks']['styles'][0]['selections'][0]['perk']
                        perk1 = joueur['perks']['styles'][0]['selections'][1]['perk']
                        perk2 = joueur['perks']['styles'][0]['selections'][2]['perk']
                        perk3 = joueur['perks']['styles'][0]['selections'][3]['perk']

                        #Secondaire
                        perk4 = joueur['perks']['styles'][1]['selections'][0]['perk']
                        perk5 = joueur['perks']['styles'][1]['selections'][1]['perk']

                        #FLAT
                        defense = joueur['perks']['statPerks']['defense']
                        flex = joueur['perks']['statPerks']['flex']
                        offense = joueur['perks']['statPerks']['offense']

                        summoner1Id = joueur['summoner1Id']
                        summoner2Id = joueur['summoner2Id']
                        #Stats de la team gagnante

                        for k in range (2):
                            en=0
                            al=0
                            u=0
                            o=0
                            banally=[]
                            banennemy=[]
                            idteams = response['info']['teams'][k]['teamId']
                            
                            if teamId == idteams:
                                #Champion:
                                nbkilltot= response['info']['teams'][k]['objectives']['champion']['kills']
                                firstblood = response['info']['teams'][k]['objectives']['champion']['first']

                                #Dragon:
                                nbdragontot=response['info']['teams'][k]['objectives']['dragon']['kills']
                                firstblooddrake=response['info']['teams'][k]['objectives']['dragon']['first']

                                #Herald:
                                nbHerald=response['info']['teams'][k]['objectives']['riftHerald']['kills']
                                firstherald=response['info']['teams'][k]['objectives']['riftHerald']['kills']

                                #Baron:
                                Nbbaron= response['info']['teams'][k]['objectives']['baron']['kills']
                                firstbaron=response['info']['teams'][k]['objectives']['baron']['first']

                                #inib:
                                nbinib=response['info']['teams'][k]['objectives']['inhibitor']['kills']
                                firstinib=response['info']['teams'][k]['objectives']['inhibitor']['first']

                                #Tower:
                                NbTower=response['info']['teams'][k]['objectives']['tower']['kills']
                                firstTower=response['info']['teams'][k]['objectives']['tower']['first']

                                #Ban
                                if len(response['info']['teams'][k]['bans'])==5:
                                    for al in range(5):
                                        banally.append(response['info']['teams'][k]['bans'][al]['championId'])

                                elif len(response['info']['teams'][k]['bans'])==4:
                                    for al in range(4):
                                        banally.append(response['info']['teams'][k]['bans'][al]['championId'])
                                    banally.append("Aucun")

                                elif len(response['info']['teams'][k]['bans'])==3:
                                    for al in range(3):
                                        banally.append(response['info']['teams'][k]['bans'][al]['championId'])
                                    banally.append("Aucun")
                                    banally.append("Aucun")
                                else:
                                    while u <5:
                                        banally.append("Aucun")
                                        u=u+1

                                if k == 0:
                                    ennemykilltot = response['info']['teams'][1]['objectives']['champion']['kills'] 
                                    ennemydraketot = response['info']['teams'][1]['objectives']['dragon']['kills'] 
                                    ennemyheraldtot =response['info']['teams'][1]['objectives']['riftHerald']['kills'] 
                                    ennemybarontot =response['info']['teams'][1]['objectives']['baron']['kills'] 
                                    ennemyinibtot =response['info']['teams'][1]['objectives']['inhibitor']['kills'] 
                                    ennemytowertot =response['info']['teams'][1]['objectives']['tower']['kills'] 
                                    for en in range(5):
                                        if len(response['info']['teams'][1]['bans'])==5:
                                            for en in range(5):
                                                banennemy.append(response['info']['teams'][1]['bans'][en]['championId'])
                                                
                                        elif len(response['info']['teams'][1]['bans'])==4:
                                            for en in range(4):
                                                banennemy.append(response['info']['teams'][1]['bans'][en]['championId'])
                                                banennemy.append("Aucun")

                                        elif len(response['info']['teams'][1]['bans'])==3:
                                            for en in range(3):
                                                banennemy.append(response['info']['teams'][1]['bans'][en]['championId'])
                                                banennemy.append("Aucun")
                                                banennemy.append("Aucun")
                                            
                                        else:
                                            while o <5:
                                                banennemy.append("Aucun")
                                                o=o+1

                                    
                                elif k == 1:
                                    ennemykilltot = response['info']['teams'][0]['objectives']['champion']['kills'] 
                                    ennemydraketot = response['info']['teams'][0]['objectives']['dragon']['kills'] 
                                    ennemyheraldtot =response['info']['teams'][0]['objectives']['riftHerald']['kills'] 
                                    ennemybarontot =response['info']['teams'][0]['objectives']['baron']['kills'] 
                                    ennemyinibtot =response['info']['teams'][0]['objectives']['inhibitor']['kills'] 
                                    ennemytowertot =response['info']['teams'][0]['objectives']['tower']['kills'] 
                                    for en in range(5):
                                        if len(response['info']['teams'][0]['bans'])==5:
                                            for en in range(5):
                                                banennemy.append(response['info']['teams'][0]['bans'][en]['championId'])
                                                
                                        elif len(response['info']['teams'][0]['bans'])==4:
                                            for en in range(4):
                                                banennemy.append(response['info']['teams'][0]['bans'][en]['championId'])
                                                banennemy.append("Aucun")

                                        elif len(response['info']['teams'][0]['bans'])==3:
                                            for en in range(3):
                                                banennemy.append(response['info']['teams'][0]['bans'][en]['championId'])
                                                banennemy.append("Aucun")
                                                banennemy.append("Aucun")
                                            
                                        else:
                                            while o <5:
                                                banennemy.append("Aucun")
                                                o=o+1



                        #Recherche dans la table les données du joueur et on les affiche 
                            

                                statsdujoueur = [Gameid,Player,Team,gameVersion,gameMode,teamId,lane,poste,championName,kills,deaths,assists,KDA,champLevel,win,item0,item1,item2,item3,item4,item5,item6,goldEarned,totalDamageDealtToChampions,totalDamageTaken,totalHeal,longestTimeSpentLiving,timeCCingOthers,CreepKill,junglemobkill,totalMinionsKill,visionScore,visionWardsBoughtInGame,wardsplaced,wardskilled,detectorWardsPlaced,timePlayed,Branch1,Branch2,perk0,perk1,perk2,perk3,perk4,perk5,defense,flex,offense,summoner1Id,summoner2Id,banally[0],banally[1],banally[2],banally[3],banally[4],banennemy[0],banennemy[1],banennemy[2],banennemy[3],banennemy[4],nbkilltot,firstblood,nbdragontot,firstblooddrake,nbHerald,firstherald,Nbbaron,firstbaron,nbinib,firstinib,NbTower,firstTower,ennemykilltot,ennemydraketot,ennemyheraldtot,ennemybarontot,ennemyinibtot,ennemytowertot,skillshotsDodged,quickCleanse,soloKills,laneMinionsFirst10Minutes,goldPerMinute,gameLength]
                                statsdujoueurfinale2.append(statsdujoueur)
                                self.insert_rows("game_stats",statsdujoueur)
        self.write_csv(Team,Player,statsdujoueurfinale2)                                

        return statsdujoueurfinale2
    

    def write_csv(self,Team,Player,statsdujoueurfinale2):
        output_dir = os.path.join("output", Team)
        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, f"{Player}_stat.csv")

        with open(csv_path, "w", newline="", encoding="utf-8", errors="ignore") as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(statsdujoueurfinale2)

        print(f"Fichier enregistré : {csv_path}")
