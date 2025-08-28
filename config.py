import logging
from logging.handlers import RotatingFileHandler

LOG_FILE_NAME = "bot.log"
PORT = '5050'
OWNER_ID = 7493303801
MSG_EFFECT = 5046509860389126442
SHORT_URL = "genzurl.com"
SHORT_API = "3dd6b17b71bd35a37ca4a5546baa5e86958a4f00"

def LOGGER(name: str, client_name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        f"[%(asctime)s - %(levelname)s] - {client_name} - %(name)s - %(message)s",
        datefmt='%d-%b-%y %H:%M:%S'
    )
    file_handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=50_000_000, backupCount=10)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
