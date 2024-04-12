"""
# Page Template - Uncomment All
"""
### begin template
# import streamlit as st
# import numpy as np
# import pandas as pd
# from io import StringIO
# import time
# from components.logger import *
# import os
# from streamlit_cognito_auth import CognitoAuthenticator
# from dotenv import load_dotenv
# from st_pages import show_pages_from_config, add_indentation, hide_pages
# st.set_page_config(
#     page_title="Palmer Lab Database",
#     page_icon="🐀",
#     layout="wide",
#     initial_sidebar_state="auto"
# )
# logger = setup_logger()
# filename = os.path.basename(__file__)

# log_action(logger, f'page: {filename}')

# dotenv_path = os.path.join(os.getcwd(), '.streamlit', 'auth.env')
# load_dotenv(dotenv_path)
# pool_id = os.environ.get("POOL_ID")
# app_client_id = os.environ.get("APP_CLIENT_ID")
# app_client_secret = os.environ.get("APP_CLIENT_SECRET")
# admin = os.environ.get("ADMIN")

# authenticator = CognitoAuthenticator(
#     pool_id=pool_id,
#     app_client_id=app_client_id,
#     app_client_secret=app_client_secret,
#     use_cookies=False
# )

# with st.sidebar:
#     is_logged_in = authenticator.login()
    
# username = authenticator.get_username()
# # sidebar pages
# add_indentation()
# show_pages_from_config()
# if not is_logged_in:
#     st.write('Please log in.')
#     hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary", "Genotyping Metadata"])
# elif is_logged_in:
#     log_action(logger, f'{filename}: authentication status: true, user name: {username}')
#     def logout():
#         authenticator.logout()
#     with st.sidebar:
#         st.write(f"Welcome, {authenticator.get_username()}!")
#         st.button("Logout", "logout_btn", on_click=logout)
#     if username != admin:
#         st.write('You do not have permission to access this page :( If you think this is a mistake, please contact us.')
#         hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary", "Genotyping Metadata"])

# with st.sidebar:
#     st.markdown('''
#     [ratgenes.org](https://ratgenes.org)
    
#     [Palmer Lab website](https://palmerlab.org)
    
#     [ratgtex.org](https://ratgtex.org)
#     ''')

# if is_logged_in and username == admin:

###
# '''
# NEW PAGE CONTENT
# '''
###