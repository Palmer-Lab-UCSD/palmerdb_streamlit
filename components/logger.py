import logging
from datetime import datetime
import streamlit as st

def setup_logger():
    # Create a logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    return logger

def log_action(logger, action):
    # Log the action
    logger.info(action)

# logger = setup_logger()
# log_action(logger, "Some action occurred")
