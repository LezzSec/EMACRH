import logging
from datetime import datetime

def log_action(action, details=""):
    logging.basicConfig(filename="logs/emac.log", level=logging.INFO)
    logging.info(f"[{datetime.now()}] {action} - {details}")
