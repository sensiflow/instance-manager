import logging

logging.basicConfig(level=logging.DEBUG)


def logError(type, e):
    logging.error(f"[ERROR {type}] " + str(e))


def logShutdown():
    logging.info("[SHUTDOWN] Shutting down the program")


def logSuccess(level: int, message: str):
    logging.info(f"[SUCCESS {level}] {message}")
