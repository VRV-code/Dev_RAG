import streamlit as st
import torch
from streamlit_pdf_viewer import pdf_viewer
from api.app.request import ask_question, get_filename
from api.app.config import config, Path

chat_dir = Path(__file__).parent.parent

# Configuration de la page Streamlit
st.set_page_config(page_title="Chatbot", page_icon="📈", layout="wide")
if "question_counter" not in st.session_state:
    st.session_state.question_counter = 0  # Initialise le compteur



class ChatBot:
    def __init__(self):
        """Initialisation du chatbot."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "pdf_selectionnee" not in st.session_state:
            st.session_state.pdf_selectionnee = None



        self.response = None

    def _select_pdf_path(self, filename):
        st.session_state.pdf_selectionnee = filename

    def _retrieve_filepaths(self, chunk):
        try:
            file_id = chunk["metadata"]["filename"]
            filename = get_filename(file_id)
            filename = filename["filename"]
        except Exception as e:
            print(f"Error {e} -> _retrieve_filepaths")
            return
        return filename

    def _display_pdf(self, filename):
        """Affiche le PDF si une réponse est disponible."""
        pdf_url = f"{config.FASTAPI_URL}/afficher/{filename}"
        pdf_display = f'<iframe src="https://mozilla.github.io/pdf.js/web/viewer.html?file={pdf_url}" width="100%" height="500px"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    def _get_chunks_set(self, chunks):
        list_of_filename = []
        for chunk in chunks:
            list_of_filename.append(chunk["filename"])

        return set(list_of_filename)


    def _display_messages(self):
        """Affiche les messages précédents du chat."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if "chunks" in message:
                    for i, filename in enumerate(self._get_chunks_set(message["chunks"])):
                        # Utilisation de la constante s'incrémentant et de la clé unique
                        unique_key = f"{filename}_{i}_{st.session_state.question_counter}"

                        st.button(
                            f"``Source{i+1}``: {filename}",
                            key=unique_key,  # Clé unique combinée avec le compteur
                            on_click=self._select_pdf_path,
                            args=(filename,),
                        )

                        st.session_state.question_counter += 1


                    # Afficher les chunks avec leurs boutons
                    with st.expander("Source"):
                        for i, chunk in enumerate(message["chunks"]):
                            st.markdown(
                                f"**Extrait {chunk['index']+1}:**\n\n *{chunk['content']}*\n\n``Source{i+1}``: {chunk['filename']}"
                            )
                            st.divider()
                else:
                    st.markdown(message["content"])

    def _handle_user_input(self):
        """Gère l'entrée de l'utilisateur et l'envoi des questions."""
        if prompt := st.chat_input("Posez votre question :"):
            # Incrémenter le compteur à chaque question posée

            # Ajouter la question de l'utilisateur à l'historique
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Obtenir la réponse via le modèle
            self.response = ask_question(prompt)

            if self.response["content"] != "Je ne sais pas":
                # Ajouter la réponse complète à l'historique
                st.session_state.messages.append(
                    {"role": "assistant", "content": self.response["content"]}
                )

                # Ajouter les chunks dans l'historique avec les boutons associés
                documents = self.response["documents"]
                chunks = []
                for index, chunk in enumerate(documents):
                    filename = self._retrieve_filepaths(chunk=chunk)
                    chunks.append(
                        {
                            "index": index,
                            "content": str(chunk["content"]),
                            "filename": filename,
                        }
                    )
                    if index ==0:
                        self._select_pdf_path(filename)

                # Ajouter les chunks à l'historique
                st.session_state.messages.append(
                    {"role": "assistant", "chunks": chunks}
                )

            else:
                # Réponse d'erreur ou non trouvée
                st.session_state.messages.append(
                    {"role": "assistant", "content": self.response["content"]}
                )

            st.rerun()

    def run(self):
        """Fonction principale du chatbot pour démarrer et afficher le chat."""
        # file_paths = self.file_manager.handle_file_upload()
        # if file_paths:
        #     st.success("Fichier chargé avec succès!")
        # else:
        #     st.warning("Vous n'avez pas chargé de fichier PDF.")

        columns = st.columns(2)
        col1 = columns[0]
        col2 = columns[1]

        with col1:
            with col1.container(border=True, height=520):
                st.subheader("CHATBOT")
                self._display_messages()  # Afficher l'historique des messages
                self._handle_user_input()  # Gérer l'entrée de l'utilisateur

        with col2:
            pdf_container = st.container()

            if st.session_state.pdf_selectionnee:
                with pdf_container:
                    self._display_pdf(st.session_state.pdf_selectionnee)
            else:
                pdf_viewer(input=chat_dir / "document.pdf", render_text=True)


def get_chatbot_instance():
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = ChatBot()
    return st.session_state.chatbot


if __name__ == "__main__":
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    chatbot = get_chatbot_instance()
    chatbot.run()
