"""
# Palmer Lab Database Dashboard Home
"""

import streamlit as st
import numpy as np
import pandas as pd
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from components.logger import *
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
# with open('config.yaml') as file:
#     config = yaml.load(file, Loader=SafeLoader)

# authenticator = stauth.Authenticate(
#     config['credentials'],
#     config['cookie']['name'],
#     config['cookie']['key'],
#     config['cookie']['expiry_days'],
#     config['preauthorized']
# )

# name, authentication_status, username = authenticator.login('sidebar')
dotenv_path = os.path.join(os.getcwd(), '.streamlit', 'auth.env')
load_dotenv(dotenv_path)
st.write(dotenv_path)
pool_id = os.environ.get("POOL_ID")
app_client_id = os.environ.get("APP_CLIENT_ID")
app_client_secret = os.environ.get("APP_CLIENT_SECRET")

authenticator = CognitoAuthenticator(
    pool_id=pool_id,
    app_client_id=app_client_id,
    app_client_secret=app_client_secret,
    use_cookies=False
)

with st.sidebar:
    is_logged_in = authenticator.login()

    
username = authenticator.get_username()
# sidebar pages
add_indentation()
show_pages_from_config()
if not is_logged_in:
    hide_pages(["Database Summary", "Sample Tracking"])
elif is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
    def logout():
        authenticator.logout()
    with st.sidebar:
        st.write(f"Welcome, {authenticator.get_username()}")
        st.button("Logout", "logout_btn", on_click=logout)
    if username != 'admin':
        hide_pages(["Database Summary", "Sample Tracking"])
# elif not is_logged_in:
#     log_action(logger, f'{filename}: authentication status: false')
#     st.error('Username/password is incorrect')
#     hide_pages(["Database Summary", "Sample Tracking"])


# title
st.image('https://ratgenes.org/wp-content/uploads/2014/11/GWAS_1200x150pxBanner-01.png')
st.write("# Palmer Lab Database 🐀")

# body
st.markdown(
    """
    This application serves as a dashboard for the Palmer Lab database.
    
    Pages:
    
    Public
    - Genotyping Report
    
    Palmer Lab Access:
    - Sample Tracking 
    - Summary

    Future:
    - project stuff
        - data dictionaries
    - visuals
    
    Links:
    - [ratgenes.org](https://ratgenes.org)
    - [Palmer Lab website](https://palmerlab.org)

    This app was created with [streamlit](https://streamlit.io).
"""
)



# # Check authentication
# authenticate.set_st_state_vars()
# # Add login/logout buttons
# if st.session_state["authenticated"]:
#     authenticate.button_logout()
# else:
#     authenticate.button_login()

# # hide pages from non-palmer lab
# if "palmerlab" not in st.session_state["user_cognito_groups"]:
    # hide_pages(["Database Summary", "Sample Tracking"])
    
# # sidebar pages
# add_indentation()
# show_pages_from_config()

# # title
# st.image('https://ratgenes.org/wp-content/uploads/2014/11/GWAS_1200x150pxBanner-01.png')
# st.write("# Palmer Lab Database 🐀")

# # body
# st.markdown(
#     """
#     This application serves as a dashboard for the Palmer Lab database.
    
#     Pages:
    
#     Public
#     - Genotyping Report
    
#     Palmer Lab Access:
#     - Sample Tracking 
#     - Summary

#     Future:
#     - project stuff
#         - data dictionaries
#     - visuals
    
#     Links:
#     - [ratgenes.org](https://ratgenes.org)
#     - [Palmer Lab website](https://palmerlab.org)

#     This app was created with [streamlit](https://streamlit.io).
# """
# )
