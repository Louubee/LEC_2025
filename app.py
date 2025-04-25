import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

# === CHARGEMENT DES DONNÉES ===
def load_data(directory):
    data = []
    if not os.path.exists(directory):  # Vérifie que le répertoire existe
        st.error(f"Le dossier {directory} n'existe pas.")
        return pd.DataFrame()

    for team_folder in os.listdir(directory):
        team_path = os.path.join(directory, team_folder)
        if os.path.isdir(team_path):  # Vérifiez que c'est bien un dossier
            for player_file in os.listdir(team_path):
                player_path = os.path.join(team_path, player_file)
                if os.path.isfile(player_path) and player_file.endswith(".csv"):  # Charger seulement les fichiers CSV
                    try:
                        player_data = pd.read_csv(player_path)
                        player_data["Team"] = team_folder  # Ajouter une colonne Team pour identifier l'équipe
                        data.append(player_data)
                    except Exception as e:
                        st.warning(f"Impossible de lire le fichier {player_path}: {e}")

    return pd.concat(data, ignore_index=True) if data else pd.DataFrame()  # Retourne un DataFrame global

# Utilisation de st.cache_data
@st.cache_data
def load_and_prepare_data(directory="output"):
    return load_data(directory)

# === APPLICATION STREAMLIT ===
def main():
    st.title("Comparateur de performances des joueurs")
    st.markdown("""
    Comparez les performances de deux joueurs en fonction de leur équipe, champion et métriques clés.
    Visualisez les données sur le KDA, le nombre de champions joués et les solo kills.
    """)

    # Charger les données
    data = load_and_prepare_data()

    # Créer deux colonnes larges pour filtrer les joueurs
    col1, col2 = st.columns([12, 12])  # Étendre les colonnes pour améliorer la visibilité des filtres

    # === ZONES DE FILTRES JOUEURS ===
    with col1:
        st.header("Joueur 1")
        team1 = st.selectbox("Équipe (Joueur 1)", options=data["Team"].unique(), key="team1")
        filtered_players1 = data[data["Team"] == team1]
        player1 = st.selectbox("Joueur (Joueur 1)", options=filtered_players1["Player"].unique(), key="player1")
        player_data1 = data[data["Player"] == player1]

    with col2:
        st.header("Joueur 2")
        team2 = st.selectbox("Équipe (Joueur 2)", options=data["Team"].unique(), key="team2")
        filtered_players2 = data[data["Team"] == team2]
        player2 = st.selectbox("Joueur (Joueur 2)", options=filtered_players2["Player"].unique(), key="player2")
        player_data2 = data[data["Player"] == player2]

    # === GRAPHIQUES KDA MOYENS ===
    st.subheader("Comparaison des KDAs moyens par champion")
    max_kda_value = max(player_data1["KDA"].max(), player_data2["KDA"].max())  # Comparer les KDA max

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)  # Deux graphiques côte à côte avec une taille plus grande

    # Joueur 1 : KDA moyen
    champion_kda1 = player_data1.groupby("Champion")["KDA"].mean()
    axes[0].bar(champion_kda1.index, champion_kda1.values, color='skyblue')
    axes[0].set_title(f"KDA de {player1}")
    axes[0].set_ylabel("KDA")
    axes[0].set_ylim(0, max_kda_value + 1)  # Même échelle Y pour les deux graphiques
    axes[0].tick_params(axis='x', rotation=45)

    # Joueur 2 : KDA moyen
    champion_kda2 = player_data2.groupby("Champion")["KDA"].mean()
    axes[1].bar(champion_kda2.index, champion_kda2.values, color='orange')
    axes[1].set_title(f"KDA de {player2}")
    axes[1].set_ylabel("KDA")  # Étiquette manquante ajoutée
    axes[1].set_ylim(0, max_kda_value + 1)
    axes[1].tick_params(axis='x', rotation=45)

    st.pyplot(fig)

    # === FILTRES CHAMPIONS CÔTE À CÔTE ===
    st.header("Analyse détaillée des champions joués")
    col1, col2 = st.columns([4, 4])  # Étendre les colonnes ici également

    with col1:
        champions1 = player_data1["Champion"].unique()
        champion1 = st.selectbox("Champion (Joueur 1)", options=champions1, key="champion1")
        champion_data1 = player_data1[player_data1["Champion"] == champion1]

    with col2:
        champions2 = player_data2["Champion"].unique()
        champion2 = st.selectbox("Champion (Joueur 2)", options=champions2, key="champion2")
        champion_data2 = player_data2[player_data2["Champion"] == champion2]

    # === GRAPHIQUES SOLO KILLS & KDA DÉTAILLÉS AVEC ÉTIQUETTES ===
    if not champion_data1.empty and not champion_data2.empty:
        max_metric_value = max(
            champion_data1["soloKills"].sum(),
            champion_data1["KDA"].mean(),
            champion_data2["soloKills"].sum(),
            champion_data2["KDA"].mean()
        ) + 1  # Pour éviter de couper les graphes sur le haut

        col1, col2 = st.columns([4, 4])  # Étendre les colonnes pour améliorer la visibilité des graphiques détaillés

        # Joueur 1
        with col1:
            st.subheader(f"{player1} sur {champion1}")
            fig1, ax1 = plt.subplots(figsize=(6, 4))  # Augmenter la taille des graphiques
            metrics1 = {
                "Solo Kills": champion_data1["soloKills"].sum(),
                "KDA": champion_data1["KDA"].mean()
            }
            bars1 = ax1.bar(metrics1.keys(), metrics1.values(), color=['orange', 'blue'])
            ax1.set_ylim(0, max_metric_value)
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width() / 2.0, height,
                         f'{height:.1f}', ha='center', va='bottom')  # Ajouter les étiquettes de données
            st.pyplot(fig1)

        # Joueur 2
        with col2:
            st.subheader(f"{player2} sur {champion2}")
            fig2, ax2 = plt.subplots(figsize=(6, 4))  # Augmenter la taille des graphiques
            metrics2 = {
                "Solo Kills": champion_data2["soloKills"].sum(),
                "KDA": champion_data2["KDA"].mean()
            }
            bars2 = ax2.bar(metrics2.keys(), metrics2.values(), color=['orange', 'blue'])
            ax2.set_ylim(0, max_metric_value)
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2.0, height,
                         f'{height:.1f}', ha='center', va='bottom')  # Ajouter les étiquettes de données
            st.pyplot(fig2)
    else:
        st.warning("Aucune donnée disponible pour l'un des joueurs ou des champions sélectionnés.")

    # === APERÇU DES DONNÉES ===
    st.header("Échantillon de données brutes")
    st.dataframe(data.head(10))

main()

# Footer
st.markdown("---")
st.markdown(
    """
    Application créée par Louube | GitHub: [repo](https://github.com/Louubee)  
    """
)