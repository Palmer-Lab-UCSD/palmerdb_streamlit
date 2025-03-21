"""
This is a tool to get metadata for genotyping from the database.
"""

import streamlit as st
import numpy as np
import pandas as pd
from components.logger import *
from components.authenticate import *
import os
import time
import string
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

log_action(logger, f'{filename}: page entered')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
else:
    st.write('Please sign in.')

if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')
    
    
if is_logged_in and admin in username:

    st.title("Metadata for Genotyping")
    st.write("Please select a pool to begin.")
    conn = st.connection("palmerdb", type="sql", autocommit=False)
    
    # for download button
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    
    pool = conn.query("select distinct pool from sample_tracking.sample_barcode_lib where pool != 'None' order by pool")
    pool = pool.pool.tolist()
    pools = st.selectbox(label='Select pool', 
                           options=pool, index = None,
                           placeholder="Choose a pool", disabled=False, label_visibility="visible", key=4)
    log_action(logger, f'pools selected: {pools}')
    
    # query text
    projects_query = f""" SELECT DISTINCT project_name
            FROM sample_tracking.sample_barcode_lib
            WHERE pool = '{pools}' 
            """
        
    projects = conn.query(projects_query)
    projects = projects.project_name.tolist()
    # projects = [p for p in projects if p != 'rattaca_colony']
    sql = f"""
            rollback;
            begin transaction;
            SELECT
                a.rfid, a.library_name, a.project_name, a.runid as flowcell_id, a.barcode, a.pcr_barcode,
                case when a.rfid LIKE '%CFW%' then 'mouse' when a.project_name like '%su_guo%' then 'zebrafish' when a.project_name like '%friedman%' then 'mouse' else 'rat' end as organism, 
                case when a.rfid LIKE '%CFW%' then 'Carworth Farms White' when a.project_name like '%friedman%' then 'Carworth Farms White' when a.project_name like '%su_guo%' then 'Ekkwill zebrafish' else 'Heterogenous stock' end as strain, 
                coalesce({', '.join([f'{string.ascii_lowercase[i]}.sex' for i, project in enumerate(projects, start=1)])}) as sex,
                coalesce({', '.join([f'{string.ascii_lowercase[i]}.coatcolor' for i, project in enumerate(projects, start=1)])}) as coatcolor,
                coalesce({', '.join([f'{string.ascii_lowercase[i]}.sires' for i, project in enumerate(projects, start=1)])}) as sires,
                coalesce({', '.join([f'{string.ascii_lowercase[i]}.dames' for i, project in enumerate(projects, start=1)])}) as dams,
                a.fastq_files
            FROM sample_tracking.sample_barcode_lib AS a
            """
    for i, (project, _) in enumerate(zip(projects, string.ascii_lowercase[1:]), start=1):
        sql += f"""
            LEFT JOIN (select rfid, sex, sires, dames, coatcolor from {project}.wfu_master) AS {string.ascii_lowercase[i]} ON a.rfid = {string.ascii_lowercase[i]}.rfid
        """
    sql += f"""
            WHERE
                a.pool = '{pools}'
        """
    log_action(logger, f'query made with: {pools}')
    org = st.multiselect(label='select organisms', 
                         options=['rat', 'mouse', 'zebrafish'], default = ['rat'],
                         placeholder="Choose organisms to include", disabled=False, label_visibility="visible", key=5)
    
    # query
    if pools is not None:
            
        if 'drop' in sql.lower() or 'commit' in sql.lower() \
                                       or 'insert' in sql.lower() \
                                       or 'delete' in sql.lower() \
                                       or 'update' in sql.lower() \
                                       or 'alter' in sql.lower()  \
                                       or 'commit' in sql.lower():
                df = pd.DataFrame([["Invalid query"]], columns=["Message"])
                st.dataframe(df)
                st.stop()
        
        df = conn.query(sql)
    
    # filter selected animals
        if org is not None:
            log_action(logger, f'animals chosen: {org}')
            df = df.loc[df.organism.isin(org)]
        st.dataframe(df)
    
        st.write(len(df), ' samples')
        
    # download
        csv = convert_df(df) 
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'{pools}_metadata_n{len(df)}_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
    
    # force refresh
    if st.button('Refresh', on_click = st.cache_data.clear()):
        log_action(logger, f'{filename}: refresh button clicked')
        st.cache_data.clear()

with st.sidebar:
    st.markdown('''
    [ratgenes.org](https://ratgenes.org)
    
    [Palmer Lab website](https://palmerlab.org)
    
    [ratgtex.org](https://ratgtex.org)
    
    Palmer Lab IRS
    ''')
    with st.container(border=True):
        st.write('##### :green[Support]')
        st.markdown("For website support, please contact the Palmer Lab, or Elaine directly at ekeung@health.ucsd.edu.")
    
    st.image('./assets/Manhattan-Black-Roboto-font-4-alt-5.png')
    st.image('https://palmerlab.org/wp-content/uploads/2019/09/palmerlab-logo.png')