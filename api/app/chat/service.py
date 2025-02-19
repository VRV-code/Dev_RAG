import os
from langchain_openai import ChatOpenAI
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain.prompts import PromptTemplate
from api.app.config import config
from llama_cpp import Llama


class LLMService:

    @staticmethod
    def _get_models(
        model_path = config.MODEL_PATH,
        n_gpu_layers=-1,
        max_tokens: int = 1024,
        streaming: bool = False,
        placeholder=None,  # streamlit
    ):
        # print(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Le fichier spécifié pour le modèle est introuvable : {model_path}"
            )
        # print(model_path)
        default_params = {
            "model_path": model_path.as_posix(),
            "chat_format": "chatml",
            "n_gpu_layers": n_gpu_layers,
            "streaming": streaming,
            "max_tokens": max_tokens,
            "streaming": streaming,
            "n_ctx": n_ctx,
            "callbacks": (
                [StreamlitCallbackHandler(placeholder)] if placeholder else None
            ),
        }

        return Llama(**default_params)

    def generate_response(self, question: str, documents, placeholder=None):
        try:
            context = "\n".join(doc["content"] for doc in documents)

            # On suppose que documents contient un dictionnaire avec un champ 'content'
            # print("\nTHE CHUNK USED IS :", context, "\n")
            # Structurer les messages pour correspondre au format attendu par le modèle
            # Instructions strictes pour le modèle
            system_prompt = (
                "Réponds uniquement à la question en te basant sur le contexte fourni. "
                "Tu es un assistant multilingue et tu dois toujours répondre dans la langue de la question. "
                "Si la réponse n'est pas présente dans le contexte, dis uniquement 'Je ne sais pas' sans ajouter autre chose."
            )

            messages = [
                # Instruction générale au modèle
                {"role": "system", "content": system_prompt},
                # Introduction au contexte
                {
                    "role": "system",
                    "content": "Voici les informations contextuelles pertinentes à utiliser pour répondre :",
                },
                # Contexte réel
                {
                    "role": "assistant",
                    "content": context,
                },
                {"role": "user", "content": question},
            ]

            model = self._get_models()
            response = model.create_chat_completion(messages=messages, temperature=0.2,top_k=20)

            # print("Réponse brute du modèle:", response)
            if response and "choices" in response and len(response["choices"]) > 0:
                text = response["choices"][0]["message"]["content"]
                print("Réponse du modèle:", text)
                return text
            else:
                print("Aucune réponse générée.")
                return "Je ne sais pas."

        except Exception as e:
            print(f"Erreur lors de la génération de la réponse : {e} -> (llmodeling)")
            raise e
