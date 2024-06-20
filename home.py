"""
# Palmer Lab Database Dashboard Home
"""

import streamlit as st
import numpy as np
import pandas as pd
from components.logger import *
from components.authenticate import *
import os
from streamlit_cognito_auth import CognitoAuthenticator
from dotenv import load_dotenv
from st_pages import show_pages_from_config, add_indentation, hide_pages
st.set_page_config(
    page_title="Palmer Lab Database",
    page_icon="🐀",
    layout="wide",
    initial_sidebar_state="auto"
)
logger = setup_logger()
filename = os.path.basename(__file__)

log_action(logger, f'{filename}: app started')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')


# title
st.image('https://ratgenes.org/wp-content/uploads/2014/11/GWAS_1200x150pxBanner-01.png')
st.header("Palmer Lab Database 🐀", divider='green')

# body
st.markdown(
    """
    The Internet Rat Server (IRS) serves as a dashboard for the Palmer Lab database.

    To access tools, please sign in with the given account using the form in the left sidebar.
    
    This app was developed as a project for the [Palmer Lab](https://palmerlab.org), and was created with [streamlit](https://streamlit.io).
"""
)

with st.container(border=True):
    st.write('##### :green[Updates]')
    updates = st.chat_message('Palmer Lab', avatar='chat.png')
    updates.write("**v1.1:** Added tools: GWAS Report Archive, Locuszoom Generator, MedPC Extractor. Sign in to access!")

with st.sidebar:
    st.markdown('''
    [ratgenes.org](https://ratgenes.org)
    
    [Palmer Lab website](https://palmerlab.org)
    
    [ratgtex.org](https://ratgtex.org)
    
    Palmer Lab IRS v1.1.0
    ''')
    
    

