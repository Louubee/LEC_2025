import psycopg2

# Connexion à PostgreSQL
conn = psycopg2.connect(
    dbname="db_lol",  
    user="postgre",         
    password="root",    
    host="localhost",                 
    port="5432"                      
)

# Création d'un curseur pour exécuter des commandes SQL
cur = conn.cursor()

# Création de la table avec les colonnes appropriées
create_table_query = """
CREATE TABLE IF NOT EXISTS game_data (
    gameid VARCHAR(50),
    player VARCHAR(100),
    team VARCHAR(100),
    game_number VARCHAR(50),
    game_version VARCHAR(50),
    teamid INT,
    lane VARCHAR(20),
    poste VARCHAR(20),
    champion VARCHAR(50),
    kills INT,
    deaths INT,
    assists INT,
    kda FLOAT,
    champ_level INT,
    win BOOLEAN,
    item0 INT,
    item1 INT,
    item2 INT,
    item3 INT,
    item4 INT,
    item5 INT,
    item6 INT,
    gold_earn INT,
    total_dmg_dealt_to_champ INT,
    total_dmg_taken INT,
    total_heal INT,
    longest_time_alive INT,
    ennemy_cc INT,
    cs_kill INT,
    jungle_minions_kills INT,
    minions_kill INT,
    vision_score INT,
    vision_wards_bought_in_game INT,
    wards_placed INT,
    wards_killed INT,
    detector_wards_placed INT,
    time_played INT,
    branch1 INT,
    branch2 INT,
    perk0 INT,
    perk1 INT,
    perk2 INT,
    perk3 INT,
    perk4 INT,
    perk5 INT,
    defense INT,
    flex INT,
    offense INT,
    summoner1id INT,
    summoner2id INT,
    ban_1_ally INT,
    ban_2_ally INT,
    ban_3_ally INT,
    ban_4_ally INT,
    ban_5_ally INT,
    ban_1_ennemy INT,
    ban_2_ennemy INT,
    ban_3_ennemy INT,
    ban_4_ennemy INT,
    ban_5_ennemy INT,
    nb_kill_team INT,
    first_blood BOOLEAN,
    nb_drake_team INT,
    first_drake BOOLEAN,
    nb_herald_team INT,
    first_herald BOOLEAN,
    nb_baron_team INT,
    first_baron BOOLEAN,
    nb_inib_team INT,
    first_inib BOOLEAN,
    nb_tower_team INT,
    first_tower BOOLEAN,
    nb_kill_opposing_team INT,
    nb_drake_opposing_team INT,
    nb_herald_opposing_team INT,
    nb_baron_opposing_team INT,
    nb_inib_opposing_team INT,
    nb_tower_opposing_team INT,
    skillshots_dodged INT,
    quick_cleanse BOOLEAN,
    solo_kills INT,
    lane_minions_first_10_minutes INT,
    gold_per_minute FLOAT,
    game_length FLOAT
);
"""

# Exécution de la requête pour créer la table
cur.execute(create_table_query)

# Committer la transaction
conn.commit()

# Fermeture de la connexion
cur.close()
conn.close()

print("Table 'game_data' créée avec succès.")
