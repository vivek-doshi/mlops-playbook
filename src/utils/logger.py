import logging
import os

def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO):
    """Function setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    # Console handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(consoleHandler)

    return logger

# Example usage available to import across pipelines
logger = setup_logger('mlops_playbook', 'mlops.log')
