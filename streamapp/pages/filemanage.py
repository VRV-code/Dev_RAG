import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os
from api.app.request import FileRequest
from api.app.config import config as cfg, EMBEDDING_MODEL


file_request = FileRequest()
st.set_page_config(page_title=None, page_icon="", layout="wide")

class FileManager:
    def __init__(self):
        # Si un fichier est déjà chargé, on le garde en mémoire
        if "file_paths" not in st.session_state:
            st.session_state.file_paths = None

    def handle_file_upload(self):
        """Gère le téléchargement et le chargement des fichiers PDF."""
        st.sidebar.title("Gestion des fichiers")

        # Si le fichier est déjà chargé et stocké dans la session, ne pas tenter de le recharger
        if st.session_state.file_paths:
            return st.session_state.file_paths

        uploaded_files = st.file_uploader(
            "Téléchargez un fichier PDF", type=["pdf"], accept_multiple_files=False
        )

        if uploaded_files:
            try:
                # Charger les données du fichier
                file_paths = file_request.add(uploaded_files)
                st.session_state.file_paths = file_paths
                st.success(
                    f"Le fichier {uploaded_files.name} a été chargé avec succès!"
                )
                return file_paths
            except Exception as e:
                st.error(f"Erreur lors du chargement du fichier : {str(e)}")
                return None
        return None


st.title("Logs du système")

# Informations de connexion à la base de données
connection_url = os.getenv("DATABASE_SYNC_URL")

# Créez le moteur SQLAlchemy
engine = create_engine(connection_url)


st.header("Logs des fichiers")

query = "SELECT * FROM files"

# Utilisez pandas pour exécuter la requête et récupérer les données dans un DataFrame
try:
    df_files = pd.read_sql_query(query, engine)
except Exception as e:
    st.error(f"Erreur lors de la récupération des données : {e}")
    st.stop()

st.subheader("Affichage des pdf")
# Affichez les données dans un tableau interactif
df_files["uid"] = df_files["uid"].astype(str)
st.dataframe(df_files)

# Convertissez le DataFrame en CSV
csv_files = df_files.to_csv(index=False).encode("utf-8")

# Ajoutez un bouton de téléchargement pour le fichier CSV
st.download_button(
    label="Télécharger les données en CSV",
    data=csv_files,
    file_name="files.csv",
    mime="text/csv",
    key="files",
)
# st.divider()
# st.subheader("Gestion des modèles d'embedding")
# with st.form("Modifier les modèles d'embedding"):
#     option = st.selectbox("Sélectionnez les modèles à utiliser", EMBEDDING_MODEL._member_names_)
#     submit = st.form_submit_button("Valider")

#     if submit:
#         cfg.EMBEDDING_MODEL = EMBEDDING_MODEL[option]
#         st.success("Modèle d'embedding modifié avec succès.")
#         st.rerun()

# st.write(f"Modèle sélectionné: {cfg.EMBEDDING_MODEL}")
# st.divider()
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
df_logs["id"] = df_logs["id"].astype(str)

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
