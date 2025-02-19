import logging
import colorlog

# Créer un gestionnaire de log avec colorlog
logger = logging.getLogger("root")
logger.setLevel(logging.INFO)  # Afficher uniquement les messages INFO et plus graves

# Créer un gestionnaire de log avec colorlog
handler = colorlog.StreamHandler()

# Créer un format avec une couleur pour INFO et ERROR
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)s:root: %(reset)s%(message)s",  # Ajout de 'INFO:root:' pour vos logs
    log_colors={
        "INFO": "blue",  # INFO en bleu
        "ERROR": "red",  # ERROR en rouge
        # Vous pouvez ajouter d'autres couleurs ici si nécessaire
    },
)
handler.setFormatter(formatter)

# Ajouter le gestionnaire au logger
logger.addHandler(handler)
