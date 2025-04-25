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


chrome_driver='C:/Program Files (x86)/chromedriver.exe'
options=Options()

#provide location where chrome stores profiles:
options.add_argument("--user-data-dir=C:/Users/brude/AppData/Local/Google/Chrome/User Data")
options.add_argument('--profile-directory=Default')
options.add_argument("--disable-proxy-certificate-handler")

#provide the profile name with which we want to open browser
browser = webdriver.Chrome(options=options)
browser.get('https://lolpros.gg/leagues/LEC/lec-winter-season-2025')
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
    

print(dictionnaire_lol)


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

