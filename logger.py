# logger.py
import logging
import os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"audiobook_converter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def info(message: str):
    logging.info(message)

def warning(message: str):
    logging.warning(message)

def error(message: str):
    logging.error(message)

def exception(message: str):
    logging.exception(message)
