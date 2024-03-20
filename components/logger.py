import logging
from datetime import datetime
import streamlit as st

log_file = 'session_start_' + datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + ".log"

def setup_logger():
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create a file handler and set the formatter
    fh = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(fh)

    return logger

def log_action(logger, action):
    # Log the action
    logger.info(action)

# Example usage:
# logger = setup_logger()
# log_action(logger, "Some action occurred")
