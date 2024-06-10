"""
# Page Template - Uncomment All
"""
### begin template

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
else:
    st.write('Please sign in.')

if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

if is_logged_in and admin in username: 

# dotenv_path = os.path.join(os.getcwd(), '.streamlit', 'auth.env')
# load_dotenv(dotenv_path)
# pool_id = os.environ.get("POOL_ID")
# app_client_id = os.environ.get("APP_CLIENT_ID")
# app_client_secret = os.environ.get("APP_CLIENT_SECRET")
# admin = os.environ.get("ADMIN")
# hidden = os.environ.get("PAGES")

# authenticator = CognitoAuthenticator(
#     pool_id=pool_id,
#     app_client_id=app_client_id,
#     app_client_secret=app_client_secret,
#     use_cookies=False
# )

# with st.sidebar:
#     is_logged_in = authenticator.login()

# username = authenticator.get_username()
# sidebar pages
# add_indentation()
# show_pages_from_config()
# if not is_logged_in:
#     hide_pages(hidden)
# elif is_logged_in:
#     log_action(logger, f'{filename}: authentication status: true, user name: {username}')
#     def logout():
#         authenticator.logout()
#     with st.sidebar:
#         st.write(f"Welcome, {authenticator.get_username()}!")
#         st.button("Logout", "logout_btn", on_click=logout)
#     if admin not in username:
#         hide_pages([hidden])
###
# '''
# NEW PAGE CONTENT
# '''
###