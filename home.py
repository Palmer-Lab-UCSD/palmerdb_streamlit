"""
# Palmer Lab Database Dashboard Home
"""

import streamlit as st
import numpy as np
import pandas as pd
import components.authenticate as authenticate
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from st_pages import show_pages_from_config, add_indentation, hide_pages
st.set_page_config(
    page_title="Palmer Lab Database",
    page_icon="🐀",
    layout="wide",
    initial_sidebar_state="auto"
)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('sidebar')

# sidebar pages
add_indentation()
if authentication_status:
    authenticator.logout('Logout', 'sidebar')
    if st.session_state["name"] == 'admin':
        show_pages_from_config()
    else:
        hide_pages(["Database Summary", "Sample Tracking"])
elif authentication_status == None:
    hide_pages(["Database Summary", "Sample Tracking"])
elif authentication_status == False:
    st.error('Username/password is incorrect')


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

