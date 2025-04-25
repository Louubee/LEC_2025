import requests,json,csv,time,os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
from urllib.request import Request, urlopen
from tqdm import tqdm
import psycopg2

api_key=""
#Ouvertur du fichier keys.json
with open("./config/keys.json") as keys:
    api_key=json.load(keys)['api_key']
headers={
    'X-Riot-Token': api_key
}

def make_request_max_limit(url,headers=None,params=None,max_retries=5):
    retries=0

    while retries<max_retries:
        try:
            response=requests.get(url,headers=headers,params=params)
            response.raise_for_status()
            print(f"Statut HTTP reçu: {response.status_code}")

            return response.json()# Si aboutissement de la requete, retourne le resultat 
        
        except requests.exceptions.HTTPError as e:
            # Si erreur de dépassement de limit :
            if response.status_code == 429:
                #Récupère le delai d'attente :
                wait_time = int(e.response.headers.get("Retry-After", 1))  # Utilise `Retry-After`
                print(f"Limite de requete dépasser. Attente pendant {wait_time} secondes . . .")
                
                #Choix esthétique
                for _ in tqdm(range(wait_time), desc="Attente . . .", unit="s"):
                    time.sleep(1)  # Attente seconde par seconde pour afficher l'augmentation de la barre'
                retries+=1
            else:
                raise e
            
        except requests.exceptions.RequestException as e:
            # Relaie egalement les autres erreurs de connexion:
            print("Erreur réseau, réessaie dans 1 secondes")
            retries +=1

    raise Exception("Nombre max de requete atteint")

#Fonction pour récupérer un dictionnaire contenant le nom, gametag, pays,role, équipe, des joueurs LEC :
def GetDictTournamenent(url):

    chrome_driver='C:/Program Files (x86)/chromedriver.exe'
    options=Options()

    #provide location where chrome stores profiles:
    options.add_argument("--user-data-dir=C:/Users/brude/AppData/Local/Google/Chrome/User Data")
    options.add_argument('--profile-directory=Default')
    options.add_argument("--disable-proxy-certificate-handler")

    #provide the profile name with which we want to open browser
    browser = webdriver.Chrome(options=options)
    browser.get(url)
    wait=WebDriverWait(browser, 20)

    #Click buton "Show all players"

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "checkbox"))).click()

    #GET PLAYER NAME AND TEAM. NB TEAM FIXE

    NULL='NULL'
    NB_TEAM=10
    nb_joueurs=0
    dictionnaire_lol = {"Player":[],"Team":[],"Role":[],"Country":[],"Summoner_name":[],"gameName":[],"tagLine":[]}

    #Boucle pour récupérer le nombre d'équipe et de joueur.
    for i in range(1,NB_TEAM+1):
        liste_participant=browser.find_elements(by=By.XPATH,value=f"(//div[@class='participant-details'])[{i}]//div[@class='member']//a[@class='name']")
        nb_joueurs=(len(liste_participant))
        for j in range(1,nb_joueurs+1):
            web_joueur=browser.find_element(by=By.XPATH,value=f"(//div[@class='participant-details'])[{i}]//div[@class='member'][{j}]//a[@class='name']")
            joueur_txt=web_joueur.text 
            joueur_txt=joueur_txt.replace(" ","-")

            web_team=browser.find_element(by=By.XPATH,value=f"(//div[@class='participants-list'])//div[@class='col col-12 col-md-4 col-lg-3 mar-b-md'][{i}]//div[@class='team-name']")
            team_txt=web_team.text
            
            dictionnaire_lol['Player'].append(joueur_txt)
            dictionnaire_lol['Team'].append(team_txt)


    #Boucle sur le nombre de joueur
    for i in range (0,len(dictionnaire_lol["Player"])):    
        joueur=dictionnaire_lol['Player'][i]
        browser.get(f"https://lolpros.gg/player/{joueur}")
        sleep(2)
        print(joueur)

        #Premier Try pour gérer les cas qui n'ont pas de summoner names (qui ne joue pas)
        try :
            #Deuxième try pour capter les cas qui ont eu beaucoup de summoner names et passer outre la balise de scroll
            try:
                web_summoner=browser.find_element(by=By.CSS_SELECTOR,value="div[class='summoner-names'] div:nth-child(1) p:nth-child(1) ")
                summoner=web_summoner.text
            except:
                web_summoner=browser.find_element(by=By.CSS_SELECTOR,value="div[class='summoner-names --scroll'] div:nth-child(1) p:nth-child(1)")
                summoner=web_summoner.text 

        #On affecte null au joueur qui n'ont pas joué en soloq
        except:
            dictionnaire_lol["Summoner_name"].append(NULL)
            dictionnaire_lol["gameName"].append(NULL)
            dictionnaire_lol["tagLine"].append(NULL)
            dictionnaire_lol["Country"].append(NULL)  
            dictionnaire_lol["Role"].append(NULL)
            print(dictionnaire_lol)
            continue
        
        dictionnaire_lol["Summoner_name"].append(summoner)
        
        #Gestion du game / line tag
        gameNamee=summoner.split("#")[0]
        tagLine=summoner.split("#")[1]

        #Game / Line Tag
        dictionnaire_lol["gameName"].append(gameNamee)
        dictionnaire_lol["tagLine"].append(tagLine)

        #Pays
        web_country=browser.find_element(by=By.CSS_SELECTOR,value="body > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > main:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(4) > div:nth-child(1) > span:nth-child(2)")
        country=web_country.text
        country=country.replace(" ","-")
        dictionnaire_lol["Country"].append(country)  

        #Role
        web_role=browser.find_element(by=By.CSS_SELECTOR,value="body > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > main:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(4) > div:nth-child(2) > span:nth-child(2)")
        role=web_role.text
        dictionnaire_lol["Role"].append(role)
            
        df = pd.DataFrame(dictionnaire_lol)

        # Écrire dans un fichier CSV
        df.to_csv("C:/Users/brude/PROJET/2025/output/dictionnaire.csv", mode='w',index=False, encoding="utf-8-sig")  
    return df
    
          

#Fonction pour obtenir le Puuid du joueur choisi afin de limité le nombre de requetes futur.

def GetPuuid(gameName,tagLine,api_key):
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={api_key}" #URL 1 qui permet de récuperer le puuid
    response1 = make_request_max_limit(url,headers)
    puuid = response1['puuid'] #Stockage du puuid
    return puuid

#Création de la fonction me permettant de récuperer une liste de game voulu sur un joueur voulu
def liste_match(puuid, api_key):
    url = f"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count=100&api_key={api_key}"
    response = make_request_max_limit(url,headers)
    return response

#Création de la fonction me permettant de récuperer une liste de game voulu sur un joueur voulu
def GetDataTimeline(match_id, api_key):
    url=f"https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={api_key}"
    response = make_request_max_limit(url,headers)
    #Ajout des infos utiles
    return response


def GetData(Player,Team,puuid,listefinale,api_key):

    conn = psycopg2.connect(
    dbname="db_lol",
    user="postgres",
    password="root",
    host="localhost"
    )
    cur = conn.cursor()
    #Création de la liste et de la première ligne qui comprend les heading
    statsdujoueurfinale2 = [['Gameid','Player','Team','Game number','Game Version','TeamId','Lane','Poste','Champion','Kills','Deaths','Assists','KDA','ChampLevel','Win','item0','item1','item2','item3','item4','item5','item6','Gold Earn','TotalDmgDealtoChamp','TotalDmgTaken','TotalHeal','LongestTimeAlive','Ennemy_CC','CS Kill','Jungle Minions Kills','Minions Kill','visionScore','visionWardsBoughtInGame','wardsplaced','wardskilled','detectorWardsPlaced','timePlayed','Branch1','Branch2','perk0','perk1','perk2','perk3','perk4','perk5','defense','flex','offense','summoner1Id','summoner2Id','Ban 1 ally','Ban 2 ally','Ban 3 ally','Ban 4 ally','Ban 5 ally','Ban 1 ennemy','Ban 2 ennemy','Ban 3 ennemy','Ban 4 ennemy','Ban 5 ennemy','Nb Kill Team','First blood','Nb Drake Team','First Drake','Nb Herald Team','First Herald','Nb Baron Team','First Baron','Nb Inib Team','First Inib','Nb Tower Team','First Tower','Nb Kill oposing Team','Nb drake Oposing Team','Nb Herald Oposing team','Nb Baron oposing team','Nb Inib Oposing team','Nb Tower Oposing Team','skillshotsDodged','quickCleanse','soloKills','laneMinionsFirst10Minutes','goldPerMinute','gameLength']]

    
    #Lancement de la boucle pour parser tout les match du joueur en question


    for i in range(len(listefinale)):
        
        Gameid=listefinale[i]
        # 0.6*100 = 60 secondes : 100 requetes max par minute.
        
        #Création de l'url
        url3 = "https://europe.api.riotgames.com/lol/match/v5/matches/"+str(listefinale[i])+"?api_key="+api_key
        response3 = make_request_max_limit(url3,headers)
        print(listefinale[i]) 

        if not listefinale or response3["info"]["gameDuration"] < 200 or response3["info"]["gameMode"]!='CLASSIC':
            break

        #Création de la boucle allant de 1 à 10 pour parser tout les joueur de la game et obtenir le bon joueur
        for l in range(10):
            puuidplayer = response3['info']['participants'][l]['puuid']#Test puuid
            #!!!! Supprimer le temps d'attente  !!!!
            #Condition pour être sur d'obteir les data du bon joueur
            if puuidplayer == puuid:
                print("Game N°",i+1)
                print(listefinale[i]) 
                numerojoueur = response3['info']['participants'][l]['participantId']-1
                
                participantid = response3['info']['participants'][numerojoueur]['participantId']-1
                
                # #Information de base sur la game 
                gameVersion = response3['info']['gameVersion']
                gameMode = response3['info']['gameMode']

                #Stats du joueur choisi 

                if participantid == numerojoueur:
                    teamId = response3['info']['participants'][numerojoueur]['teamId']
                    lane = response3['info']['participants'][numerojoueur]['lane']
                    poste = response3['info']['participants'][numerojoueur]['individualPosition']
                    championName = response3['info']['participants'][numerojoueur]['championName']
                    skillshotsDodged=response3["info"]["participants"][numerojoueur]["challenges"]["skillshotsDodged"]
                    quickCleanse=response3["info"]["participants"][numerojoueur]["challenges"]["quickCleanse"]
                    soloKills=response3["info"]["participants"][numerojoueur]["challenges"]["soloKills"]
                    laneMinionsFirst10Minutes=response3["info"]["participants"][numerojoueur]["challenges"]["laneMinionsFirst10Minutes"]
                    goldPerMinute=response3["info"]["participants"][numerojoueur]["challenges"]["goldPerMinute"]
                    gameLength=response3["info"]["participants"][numerojoueur]["challenges"]["gameLength"]

                    kills = response3['info']['participants'][numerojoueur]['kills']
                    deaths = response3['info']['participants'][numerojoueur]['deaths']
                    assists = response3['info']['participants'][numerojoueur]['assists']
                    if deaths >0:
                        KDA = round((response3['info']['participants'][numerojoueur]['kills'] + response3['info']['participants'][numerojoueur]['assists'])/response3['info']['participants'][numerojoueur]['deaths'],2)
                    else:
                        KDA = round((response3['info']['participants'][numerojoueur]['kills'] + response3['info']['participants'][numerojoueur]['assists']),2)
                    champLevel =  response3['info']['participants'][numerojoueur]['champLevel']
                    win = response3['info']['participants'][numerojoueur]['win']

                    #Gold
                    item0 = response3['info']['participants'][numerojoueur]['item0']
                    item1 = response3['info']['participants'][numerojoueur]['item1']
                    item2 = response3['info']['participants'][numerojoueur]['item2']
                    item3 = response3['info']['participants'][numerojoueur]['item3']
                    item4 = response3['info']['participants'][numerojoueur]['item4']
                    item5 = response3['info']['participants'][numerojoueur]['item5']
                    item6 = response3['info']['participants'][numerojoueur]['item6']
                    goldEarned = response3['info']['participants'][numerojoueur]['goldEarned']

                    #STATS du joueur :
                    
                    #Graph
                    totalDamageDealtToChampions = response3['info']['participants'][numerojoueur]['totalDamageDealtToChampions']
                    totalDamageTaken = response3['info']['participants'][numerojoueur]['totalDamageTaken']
                    totalHeal = response3['info']['participants'][numerojoueur]['totalHeal'] 
                    longestTimeSpentLiving = response3['info']['participants'][numerojoueur]['longestTimeSpentLiving']
                    timeCCingOthers = response3['info']['participants'][numerojoueur]['timeCCingOthers']

                    #CSing
                    CreepKill =  response3['info']['participants'][numerojoueur]['totalMinionsKilled']
                    junglemobkill = response3['info']['participants'][numerojoueur]['neutralMinionsKilled']
                    totalMinionsKill = response3['info']['participants'][numerojoueur]['totalMinionsKilled'] + response3['info']['participants'][numerojoueur]['neutralMinionsKilled']
                

                    #Vision

                    visionScore = response3['info']['participants'][numerojoueur]['visionScore'] 
                    visionWardsBoughtInGame =  response3['info']['participants'][numerojoueur]['visionWardsBoughtInGame']
                    wardsplaced = response3['info']['participants'][numerojoueur]['wardsPlaced']
                    wardskilled = response3['info']['participants'][numerojoueur]['wardsKilled']
                    detectorWardsPlaced = response3['info']['participants'][numerojoueur]['detectorWardsPlaced']


                    timePlayed = response3['info']['participants'][numerojoueur]['timePlayed']/60

                    #RUNES 

                    #Branche de rune
                    Branch1 = response3['info']['participants'][numerojoueur]['perks']['styles'][0]['style']
                    Branch2 = response3['info']['participants'][numerojoueur]['perks']['styles'][1]['style']

                    #Primaire
                    perk0 = response3['info']['participants'][numerojoueur]['perks']['styles'][0]['selections'][0]['perk']
                    perk1 = response3['info']['participants'][numerojoueur]['perks']['styles'][0]['selections'][1]['perk']
                    perk2 = response3['info']['participants'][numerojoueur]['perks']['styles'][0]['selections'][2]['perk']
                    perk3 = response3['info']['participants'][numerojoueur]['perks']['styles'][0]['selections'][3]['perk']

                    #Secondaire
                    perk4 = response3['info']['participants'][numerojoueur]['perks']['styles'][1]['selections'][0]['perk']
                    perk5 = response3['info']['participants'][numerojoueur]['perks']['styles'][1]['selections'][1]['perk']

                    #FLAT
                    defense = response3['info']['participants'][numerojoueur]['perks']['statPerks']['defense']
                    flex = response3['info']['participants'][numerojoueur]['perks']['statPerks']['flex']
                    offense = response3['info']['participants'][numerojoueur]['perks']['statPerks']['offense']

                    summoner1Id = response3['info']['participants'][numerojoueur]['summoner1Id']
                    summoner2Id = response3['info']['participants'][numerojoueur]['summoner2Id']
                    #Stats de la team gagnante

                    for k in range (2):
                        en=0
                        al=0
                        u=0
                        o=0
                        banally=[]
                        banennemy=[]
                        idteams = response3['info']['teams'][k]['teamId']
                        
                        if teamId == idteams:
                            #Champion:
                            nbkilltot= response3['info']['teams'][k]['objectives']['champion']['kills']
                            firstblood = response3['info']['teams'][k]['objectives']['champion']['first']

                            #Dragon:
                            nbdragontot=response3['info']['teams'][k]['objectives']['dragon']['kills']
                            firstblooddrake=response3['info']['teams'][k]['objectives']['dragon']['first']

                            #Herald:
                            nbHerald=response3['info']['teams'][k]['objectives']['riftHerald']['kills']
                            firstherald=response3['info']['teams'][k]['objectives']['riftHerald']['kills']

                            #Baron:
                            Nbbaron= response3['info']['teams'][k]['objectives']['baron']['kills']
                            firstbaron=response3['info']['teams'][k]['objectives']['baron']['first']

                            #inib:
                            nbinib=response3['info']['teams'][k]['objectives']['inhibitor']['kills']
                            firstinib=response3['info']['teams'][k]['objectives']['inhibitor']['first']

                            #Tower:
                            NbTower=response3['info']['teams'][k]['objectives']['tower']['kills']
                            firstTower=response3['info']['teams'][k]['objectives']['tower']['first']

                            #Ban
                            if len(response3['info']['teams'][k]['bans'])==5:
                                for al in range(5):
                                    banally.append(response3['info']['teams'][k]['bans'][al]['championId'])

                            elif len(response3['info']['teams'][k]['bans'])==4:
                                for al in range(4):
                                    banally.append(response3['info']['teams'][k]['bans'][al]['championId'])
                                banally.append("Aucun")

                            elif len(response3['info']['teams'][k]['bans'])==3:
                                for al in range(3):
                                    banally.append(response3['info']['teams'][k]['bans'][al]['championId'])
                                banally.append("Aucun")
                                banally.append("Aucun")
                            else:
                                while u <5:
                                    banally.append("Aucun")
                                    u=u+1
                            print(k)

                            if k == 0:
                                ennemykilltot = response3['info']['teams'][1]['objectives']['champion']['kills'] 
                                ennemydraketot = response3['info']['teams'][1]['objectives']['dragon']['kills'] 
                                ennemyheraldtot =response3['info']['teams'][1]['objectives']['riftHerald']['kills'] 
                                ennemybarontot =response3['info']['teams'][1]['objectives']['baron']['kills'] 
                                ennemyinibtot =response3['info']['teams'][1]['objectives']['inhibitor']['kills'] 
                                ennemytowertot =response3['info']['teams'][1]['objectives']['tower']['kills'] 
                                for en in range(5):
                                    if len(response3['info']['teams'][1]['bans'])==5:
                                        for en in range(5):
                                            banennemy.append(response3['info']['teams'][1]['bans'][en]['championId'])
                                            
                                    elif len(response3['info']['teams'][1]['bans'])==4:
                                        for en in range(4):
                                            banennemy.append(response3['info']['teams'][1]['bans'][en]['championId'])
                                            banennemy.append("Aucun")

                                    elif len(response3['info']['teams'][1]['bans'])==3:
                                        for en in range(3):
                                            banennemy.append(response3['info']['teams'][1]['bans'][en]['championId'])
                                            banennemy.append("Aucun")
                                            banennemy.append("Aucun")
                                        
                                    else:
                                        while o <5:
                                            banennemy.append("Aucun")
                                            o=o+1

                                
                            elif k == 1:
                                ennemykilltot = response3['info']['teams'][0]['objectives']['champion']['kills'] 
                                ennemydraketot = response3['info']['teams'][0]['objectives']['dragon']['kills'] 
                                ennemyheraldtot =response3['info']['teams'][0]['objectives']['riftHerald']['kills'] 
                                ennemybarontot =response3['info']['teams'][0]['objectives']['baron']['kills'] 
                                ennemyinibtot =response3['info']['teams'][0]['objectives']['inhibitor']['kills'] 
                                ennemytowertot =response3['info']['teams'][0]['objectives']['tower']['kills'] 
                                for en in range(5):
                                    if len(response3['info']['teams'][0]['bans'])==5:
                                        for en in range(5):
                                            banennemy.append(response3['info']['teams'][0]['bans'][en]['championId'])
                                            
                                    elif len(response3['info']['teams'][0]['bans'])==4:
                                        for en in range(4):
                                            banennemy.append(response3['info']['teams'][0]['bans'][en]['championId'])
                                            banennemy.append("Aucun")

                                    elif len(response3['info']['teams'][0]['bans'])==3:
                                        for en in range(3):
                                            banennemy.append(response3['info']['teams'][0]['bans'][en]['championId'])
                                            banennemy.append("Aucun")
                                            banennemy.append("Aucun")
                                        
                                    else:
                                        while o <5:
                                            banennemy.append("Aucun")
                                            o=o+1



                    #Recherche dans la table les données du joueur et on les affiche 
                        

                            statsdujoueur = [Gameid,Player,Team,gameVersion,gameMode,teamId,lane,poste,championName,kills,deaths,assists,KDA,champLevel,win,item0,item1,item2,item3,item4,item5,item6,goldEarned,totalDamageDealtToChampions,totalDamageTaken,totalHeal,longestTimeSpentLiving,timeCCingOthers,CreepKill,junglemobkill,totalMinionsKill,visionScore,visionWardsBoughtInGame,wardsplaced,wardskilled,detectorWardsPlaced,timePlayed,Branch1,Branch2,perk0,perk1,perk2,perk3,perk4,perk5,defense,flex,offense,summoner1Id,summoner2Id,banally[0],banally[1],banally[2],banally[3],banally[4],banennemy[0],banennemy[1],banennemy[2],banennemy[3],banennemy[4],nbkilltot,firstblood,nbdragontot,firstblooddrake,nbHerald,firstherald,Nbbaron,firstbaron,nbinib,firstinib,NbTower,firstTower,ennemykilltot,ennemydraketot,ennemyheraldtot,ennemybarontot,ennemyinibtot,ennemytowertot,skillshotsDodged,quickCleanse,soloKills,laneMinionsFirst10Minutes,goldPerMinute,gameLength]

                    
                #Ajout des stats dans la table crée précedemment
                            statsdujoueurfinale2.append(statsdujoueur)
                            cur.execute("""INSERT INTO game_stats (
                gameid,player,team,game_number,game_version,teamid,lane,poste,champion,kills,deaths,assists,kda,champlevel,win,item0,item1
                ,item2,item3,item4,item5,item6,gold_earn,totaldmgdealtochamp,totaldmgtaken,totalheal,longesttimealive,ennemy_cc,cs_kill
                ,jungle_minions_kills,minions_kill,visionscore,visionwardsboughtingame,wardsplaced,wardskilled,detectorwardsplaced
                ,timeplayed,branch1,branch2,perk0,perk1,perk2,perk3,perk4,perk5,defense,flex,offense,summoner1id,summoner2id
                ,ban_1_ally,ban_2_ally,ban_3_ally,ban_4_ally,ban_5_ally,ban_1_ennemy,ban_2_ennemy,ban_3_ennemy,ban_4_ennemy,ban_5_ennemy
                ,nb_kill_team,first_blood,nb_drake_team,first_drake,nb_herald_team,first_herald,nb_baron_team,first_baron,nb_inib_team,first_inib
                ,nb_tower_team,first_tower,nb_kill_oposing_team,nb_drake_oposing_team,nb_herald_oposing_team,nb_baron_oposing_team,nb_inib_oposing_team
                ,nb_tower_oposing_team,skillshotsdodged,quickcleanse,solokills,laneminionsfirst10minutes,goldperminute,gamelength
                ) 
                VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,%s, %s, %s, %s
                ) ON CONFLICT DO NOTHING""",statsdujoueur)

                conn.commit()
                    
        

    #Création d'un CSV pour y stocker les data  
    output_dir = os.path.join("output", Team)
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"{Player}_stat.csv")

    with open(csv_path, "w", newline="", encoding="utf-8", errors="ignore") as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(statsdujoueurfinale2)

    print(f"Fichier enregistré : {csv_path}")
    
    # Fermeture
    cur.close()
    conn.close()

    return statsdujoueurfinale2
