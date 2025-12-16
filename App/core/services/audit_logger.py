import logging
from datetime import datetime
from core.utils.app_paths import get_log_file_path

def log_action(action, details=""):
    log_file = get_log_file_path("emac.log")
    logging.basicConfig(filename=str(log_file), level=logging.INFO)
    logging.info(f"[{datetime.now()}] {action} - {details}")
