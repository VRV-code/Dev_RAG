# controllers.py
import requests
from io import BytesIO
from api.app import logger
from uuid import UUID
from api.app.config import config
from huggingface_hub import hf_hub_download

class LLMRequest:
    def add(self, repo_id, llmname):
        # Préparation des données à envoyer
        llm_path = hf_hub_download(
            repo_id=repo_id,
            llmname=llmname,
            local_dir= config.MODEL_FOLDER,  # Répertoire de destination
            local_dir_use_symlinks=False  # Désactive l'utilisation des liens symboliques
        )

        # Point de terminaison de l'API
        url = f"{config.FASTAPI_URL}/create_llm"

        print(f"Envoi du fichier {llmname} à {url}")
        try:
            # Requête POST pour envoyer le fichier
            response = requests.post(url, files=llmname, timeout=180)
            response.raise_for_status()  # Lève une exception pour les codes HTTP d'erreur

            # Vérification de la réponse
            if response.status_code == 201:
                print("Fichier traité avec succès !")
                return response.json()
            else:
                print(f"Erreur HTTP {response.status_code} : {response.text}")
                return None
        except requests.Timeout:
            logger.error("Le serveur met trop de temps à répondre.")
            print("Le serveur met trop de temps à répondre.")
        except requests.ConnectionError:
            logger.error("Impossible de se connecter au serveur.")
            print("Impossible de se connecter au serveur.")
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la requête : {e}")
            print(f"Erreur lors de la requête : {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            print(f"Erreur inattendue : {e}")
            return None

    def llmdelete(self, file_ids: list[str]):

        if not file_ids:
            return False

        try:
            response = requests.delete(
                url=f"{config.FASTAPI_URL}/delete_llm",
                json=file_ids,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()  # Lève une exception pour les codes HTTP d'erreur

            # Vérification de la réponse
            if response.status_code == 201:
                print("Fichier traité avec succès !")
                return response
            else:
                return None
        except requests.Timeout:
            logger.error("Le serveur met trop de temps à répondre.")
            print("Le serveur met trop de temps à répondre.")
        except requests.ConnectionError:
            logger.error("Impossible de se connecter au serveur.")
            print("Impossible de se connecter au serveur.")
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la requête : {e}")
            print(f"Erreur lors de la requête : {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            print(f"Erreur inattendue : {e}")
            return None


class FileRequest:
    def add(self, uploaded_file):
        # Préparation des données à envoyer
        files = {
            "file_data": (
                uploaded_file.name,
                BytesIO(uploaded_file.getvalue()),  # Lire le contenu du fichier
                uploaded_file.type,  # Type MIME du fichier
            )
        }

        # Point de terminaison de l'API
        url = f"{config.FASTAPI_URL}/create_file"

        print(f"Envoi du fichier {uploaded_file.name} à {url}")
        try:
            # Requête POST pour envoyer le fichier
            response = requests.post(url, files=files, timeout=180)
            response.raise_for_status()  # Lève une exception pour les codes HTTP d'erreur

            # Vérification de la réponse
            if response.status_code == 201:
                print("Fichier traité avec succès !")
                return response.json()
            else:
                print(f"Erreur HTTP {response.status_code} : {response.text}")
                return None
        except requests.Timeout:
            logger.error("Le serveur met trop de temps à répondre.")
            print("Le serveur met trop de temps à répondre.")
        except requests.ConnectionError:
            logger.error("Impossible de se connecter au serveur.")
            print("Impossible de se connecter au serveur.")
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la requête : {e}")
            print(f"Erreur lors de la requête : {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            print(f"Erreur inattendue : {e}")
            return None

    def delete(self, file_ids: list[str]):

        if not file_ids:
            return False

        try:
            response = requests.delete(
                url=f"{config.FASTAPI_URL}/delete_files",
                json=file_ids,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()  # Lève une exception pour les codes HTTP d'erreur

            # Vérification de la réponse
            if response.status_code == 201:
                print("Fichier traité avec succès !")
                return response
            else:
                return None
        except requests.Timeout:
            logger.error("Le serveur met trop de temps à répondre.")
            print("Le serveur met trop de temps à répondre.")
        except requests.ConnectionError:
            logger.error("Impossible de se connecter au serveur.")
            print("Impossible de se connecter au serveur.")
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la requête : {e}")
            print(f"Erreur lors de la requête : {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            print(f"Erreur inattendue : {e}")
            return None


def ask_question(question, placeholder=None):
    """Demande une question au modèle et génère une réponse"""
    try:
        response = requests.post(
            f"{config.FASTAPI_URL}/chat/",
            json={"content": question},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()  # Lève une exception pour les erreurs HTTP
        return response.json()
    except requests.Timeout:
        logger.error("Le serveur a mis trop de temps à répondre.")
        return
    except requests.ConnectionError:
        logger.error("Impossible de se connecter au serveur.")
        return
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la requête : {e}")
        return


def get_filename(file_id: str):
    """
    Récupère le fichier correspondant à l'ID donné via une requête à l'API FastAPI.

    Args:
        file_id (str): L'ID du fichier à récupérer.

    Returns:
        dict: Les données du fichier (si récupérées avec succès).
        None: En cas d'erreur ou si le fichier n'est pas trouvé.

    Raises:
        Exception: Toute autre exception inattendue.
    """
    base_url = f"{config.FASTAPI_URL}/files"
    try:
        # Construction de l'URL complète
        url = f"{base_url}/{file_id}"

        # Effectuer la requête GET
        response = requests.get(
            url,
            headers={"Content-Type": "application/json"},
            timeout=10,  # Timeout en secondes
        )

        # Vérification du statut HTTP
        response.raise_for_status()

        # Retourner les données JSON si la requête est réussie
        return response.json()

    except requests.exceptions.Timeout:
        logger.error(
            f"Le serveur a mis trop de temps à répondre pour le fichier ID {file_id}."
        )
        return None

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            logger.warning(f"Fichier non trouvé pour l'ID {file_id}.")
        else:
            logger.error(
                f"Erreur HTTP {response.status_code} pour l'ID {file_id} : {http_err}"
            )
        return None

    except requests.exceptions.ConnectionError:
        logger.error(
            "Impossible de se connecter au serveur. Vérifiez que l'API est en cours d'exécution."
        )
        return None

    except Exception as e:
        logger.exception(f"Une erreur inattendue est survenue : {e}")
        return None
