"""
# This page is a dashboard to view data dictionaries.
"""

import streamlit as st
import numpy as np
import pandas as pd
from io import StringIO
import time
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

log_action(logger, f'page: {filename}')

dotenv_path = os.path.join(os.getcwd(), '.streamlit', 'auth.env')
load_dotenv(dotenv_path)
pool_id = os.environ.get("POOL_ID")
app_client_id = os.environ.get("APP_CLIENT_ID")
app_client_secret = os.environ.get("APP_CLIENT_SECRET")
admin = os.environ.get("ADMIN")

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
    hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary", "Genotyping Metadata"])
elif is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
    def logout():
        authenticator.logout()
    with st.sidebar:
        st.write(f"Welcome, {authenticator.get_username()}!")
        st.button("Logout", "logout_btn", on_click=logout)
    if admin not in username:
        st.write('hello')
        hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary", "Genotyping Metadata"])


if is_logged_in and admin in username:
    st.title('Data Dictionary')
    
    conn = st.connection("palmerdb", type="sql", autocommit=False)
    log_action(logger, f'{filename}: database connection made')
    
    # project list
    project = conn.query("select project_name from sample_tracking.project_metadata order by project_name")
    project = project.project_name.tolist()
    project = [p for p in project if '0' in p]
    project = sorted(project)
    log_action(logger, f'{filename}: project list acquired')
    
    # for download button
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    
    
    tab1, tab2 = st.tabs(["Data Dictionary by Project", "Search by Trait"])
    
    # dd by project
    with tab1:
        log_action(logger, f'{filename}: select tab1 data dictionary by project')
        option = st.selectbox(
            'Select project: ',
            (project),
            index=None)
        
        if option is not None:
            log_action(logger, f'project selected {option}')
            try:
                df = pd.read_csv(f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{option}/data_dict_{option}.csv')
                st.dataframe(df)
                st.write('Total traits: ', len(df))
                st.download_button(
                    label="Download data dictionary as CSV",
                    data=convert_df(df),
                    file_name=f'n{len(df)}_data_dictionary_{time.strftime("%Y%m%d")}.csv',
                    mime='text/csv',
                )
            except: st.write('Data dictionary not found. Try another project.')
    
        
    
    
    with tab2:
        log_action(logger, f'{filename}: select tab2 search traits')
        st.write('Search all traits:')
        data = pd.DataFrame()
        for p in project:
            try:
                dd = pd.read_csv(f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{p}/data_dict_{p}.csv')
                dd['project'] = p
                data = pd.concat([data, dd])
            except: continue
        
        data = data.iloc[:, :6]
        trait = st.text_input('Find a trait:', placeholder = 'Enter characters in trait name (e.g. "loco")...')
        log_action(logger, f'trait searched: {trait}')
        
        data = data.loc[data.measure.str.contains(trait)]
        st.dataframe(data)
        st.write('Total traits: ', len(data))
    
        st.download_button(
            label="Download data dictionary as CSV",
            data=convert_df(data),
            file_name=f'n{len(data)}_traits_dictionary_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
        
with st.sidebar:
    st.markdown('''
    [ratgenes.org](https://ratgenes.org)
    
    [Palmer Lab website](https://palmerlab.org)
    
    [ratgtex.org](https://ratgtex.org)
    ''')
