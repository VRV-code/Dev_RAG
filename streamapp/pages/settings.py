import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from api.app.request import LLMRequest


llm_request = LLMRequest()
st.set_page_config(page_title=None, page_icon="", layout="wide")

class LLMManager:
    def __init__(self):
        # Si un fichier est déjà chargé, on le garde en mémoire
        if "llm_paths" not in st.session_state:
            st.session_state.llm_paths = None

    def handle_llm_upload(self):
        """Gère le téléchargement et le chargement de llm."""
        st.sidebar.title("Gestion des llm")

        # Si le fichier est déjà chargé et stocké dans la session, ne pas tenter de le recharger
        if st.session_state.llm_paths:
            return st.session_state.llm_paths


        
        uploaded_repertory = st.text_input(label= 'nom du répertoire', value= '')

        uploaded_llm = st.text_input(label= 'LLM en GGUF', value= '')

        if uploaded_repertory:
            try:
                # Charger les données du fichier
                llm_paths = llm_request.add(uploaded_repertory, uploaded_llm)
                st.session_state.llm_paths = file_paths
                st.success(
                    f"Le fichier {uploaded_llm} a été chargé avec succès!"
                )
                return llm_paths
            except Exception as e:
                st.error(f"Erreur lors du chargement du fichier : {str(e)}")
                return None
        return None


st.title("Logs du système")

# Informations de connexion à la base de données
connection_url = os.getenv("DATABASE_SYNC_URL")



query = "SELECT * FROM llm"

# Utilisez pandas pour exécuter la requête et récupérer les données dans un DataFrame
try:
    df_llm = pd.read_sql_query(query, engine)
except Exception as e:
    st.error(f"Erreur lors de la récupération des données : {e}")
    st.stop()



st.subheader("Ajout de pdf")
file_paths = FileManager().handle_file_upload()
if file_paths:
    st.success("Fichier chargé avec succès!")
else:
    st.warning("Vous n'avez pas chargé de fichier PDF.")


st.subheader("Supression d'un pdf")


# st.info("This is a purely informational message", icon="ℹ️")
@st.dialog("Valider la suppression du fichier")
def validate_delete(file_names: list[str]):
    """
    Affiche une boîte de dialogue pour confirmer la suppression d'un fichier.
    """
    st.write(f"Êtes-vous sûr de vouloir supprimer les fichiers `{file_names}` ?")
    file_ids_strip = []
    file_ids = df_files[df_files["filename"].isin(file_names)]["uid"].values
    for id in file_ids:
        id_strip = str(id).strip()
        file_ids_strip.append(id_strip)

    col1, col2 = st.columns(2)
    with col1:
        confirm = st.button("Oui, supprimer")
    with col2:
        cancel = st.button("Non, annuler")

    if confirm:
        # Suppression du fichier
        file_request.delete(file_ids_strip)
        st.success(f"Les fichiers {file_names}` ont été supprimés avec succès.")
        st.rerun()
    elif cancel:
        st.info("Suppression annulée.")
        st.rerun()


# Formulaire principal pour entrer l'ID du fichier à supprimer


with st.form("Supprimer un fichier"):
    file_names = st.multiselect(
        "Entrez l'ID du fichier à supprimer", df_files["filename"].values
    )
    submitted = st.form_submit_button("Soumettre")

    if submitted:
        if file_names:
            validate_delete(file_names)

        else:
            st.error("Veuillez entrer un ID valide.")


st.divider()

st.header("Logs des requêtes antérieures")
# Requête SQL pour récupérer les données
query = "SELECT * FROM chat_logs"

# Utilisez pandas pour exécuter la requête et récupérer les données dans un DataFrame
try:
    df_logs = pd.read_sql_query(query, engine)
except Exception as e:
    st.error(f"Erreur lors de la récupération des données : {e}")
    st.stop()

# Affichez les données dans un tableau interactif
st.dataframe(df_logs)

# Convertissez le DataFrame en CSV
csv_logs = df_logs.to_csv(index=False).encode("utf-8")

# Ajoutez un bouton de téléchargement pour le fichier CSV
st.download_button(
    label="Télécharger les données en CSV",
    data=csv_logs,
    file_name="chat_logs.csv",
    mime="text/csv",
    key="chat_logs",
)

st.divider()
