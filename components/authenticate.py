import os
import streamlit as st
from dotenv import load_dotenv
from streamlit_cognito_auth import CognitoAuthenticator
from st_pages import show_pages_from_config, add_indentation, hide_pages
import requests
import base64
import json

# Read constants from environment file
def start_auth():
    dotenv_path = os.path.join(os.getcwd(), '.streamlit', 'auth.env')
    load_dotenv(dotenv_path)
    pool_id = os.environ.get("POOL_ID")
    app_client_id = os.environ.get("APP_CLIENT_ID")
    app_client_secret = os.environ.get("APP_CLIENT_SECRET")
    admin = os.environ.get("ADMIN")
    hidden = os.environ.get("PAGES")

    authenticator = CognitoAuthenticator(
        pool_id=pool_id,
        app_client_id=app_client_id,
        app_client_secret=app_client_secret,
        use_cookies=False
    )
    
    with st.sidebar:
        is_logged_in = authenticator.login()

    username = authenticator.get_username()
    
    add_indentation()
    show_pages_from_config()
    if not is_logged_in:
        hide_pages(hidden)
    elif is_logged_in and admin not in username:
        hide_pages(hidden)
        # log_action(logger, f'{filename}: authentication status: true, user name: {username}')
        def logout():
            authenticator.logout()
        with st.sidebar:
            st.write(f"Welcome, {authenticator.get_username()}!")
            st.button("Logout", "logout_btn", on_click=logout)
            
    elif is_logged_in and admin in username:
        def logout():
            authenticator.logout()
        with st.sidebar:
            st.write(f"Welcome, {authenticator.get_username()}!")
            st.button("Logout", "logout_btn", on_click=logout)
    
    return authenticator, username, hidden, admin, is_logged_in
