import streamlit as st

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Page d'accueil - Chatbot IA",
    page_icon="🤖",
    initial_sidebar_state="expanded",
)


# Fonction principale pour la page d'accueil
def main():
    # Affichage du titre et sous-titre
    st.title("Bienvenue sur votre Assistant IA 🤖")
    st.markdown(
        """
        ### 💡 Fonctionnalités principales :
        1. **Charger des fichiers PDF** : Analysez vos documents pour poser des questions directement.
        2. **Poser des questions** : Utilisez notre IA avancée pour obtenir des réponses précises et multilingues.
        3. **Visualiser et surligner les résultats** : Les réponses sont liées directement aux parties pertinentes des documents.
        """
    )

    # Ajout de colonnes pour navigation
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📂 Charger des documents")
        st.write("Téléchargez vos fichiers PDF pour commencer l'analyse.")

    with col2:
        st.subheader("💬 Poser une question")
        st.write("Demandez à l'IA n'importe quelle question.")

    with col3:
        st.subheader("📊 Voir les résultats")
        st.write("Explorez les documents avec des réponses surlignées.")

    # Footer ou informations supplémentaires
    st.markdown("---")
    st.markdown(
        """
        **À propos :** Cette application utilise les technologies avancées de RAG (Retrieval-Augmented Generation) pour combiner la puissance des grands modèles de langage avec des bases documentaires contextuelles.
        """
    )


# Exécuter la page
if __name__ == "__main__":
    main()
