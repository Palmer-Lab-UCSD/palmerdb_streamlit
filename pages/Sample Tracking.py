"""
# This page is a dashboard for the sample tracking tables in the database.
"""

import streamlit as st
import numpy as np
import pandas as pd
import time
import hmac
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

log_action(logger, f'{filename}: page entered')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
else:
    st.write('Please sign in.')

if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

if is_logged_in and admin in username:

    st.title('Palmer Lab Database Samples')
    
    # for download button
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    
    # db connection
    # creds in secret
    conn = st.connection("palmerdb", type="sql", autocommit=False)
    log_action(logger, f'{filename}: db connection made')
    # project list
    project = conn.query("select project_name from sample_tracking.project_metadata order by project_name")
    project = project.project_name.tolist()
    log_action(logger, f'{filename}: project list acquired')
    # pool list
    pool = conn.query("select distinct pool from sample_tracking.sample_barcode_lib where pool != 'None' order by pool")
    pool = pool.pool.tolist()
    log_action(logger, f'{filename}: pool list acquired')

    # project selector, rfid filter
    projects = st.multiselect(label='select project', 
                       options=project, default=None, 
                       placeholder="Choose projects", disabled=False, label_visibility="visible", key=1)
    projects = ','.join([f"'{project}'" for project in projects])
    rfids = st.text_input('find rfids', key=2)
    rfids =  ', '.join([f"'{v.strip()}'" for v in rfids.split(',') if v.strip()])

    def build_query(table, options=None, value=None, value2=None, value3=None):
        ''' 
        function that builds an sql query based on user input in up to 4 fields
        being project, rfid, runid (for barcode), pool (for barcode)
        '''
        conditions = []
    
        if options:
            log_action(logger, f'{filename}: projects selected: {options}')
            conditions.append(f"project_name IN ({options})")
    
        if value and value2:
            log_action(logger, f'{filename}: rfids selected: {value}, runid selected {value2}')
            conditions.append(f"rfid IN ({value}) AND runid = {value2}")
        elif value:
            log_action(logger,  f'{filename}: rfids selected: {value}')
            conditions.append(f"rfid IN ({value})")
        elif value2:
            log_action(logger,  f'{filename}: runid selected: {value2}')
            conditions.append(f"runid = {value2}")
        if value3:
            log_action(logger,  f'{filename}: pool selected: {value3}')
            conditions.append(f"pool IN ({value3})")
            
        query = f"SELECT * FROM sample_tracking.{table}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        return query

    # tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Sample Metadata", "DNA Extraction Log", "Sample Barcodes", 
                                                        'Tissue Received', 'Genotyping Logs', 'RNA Received', 'RNA Extraction Log'])

    # sample metadata
    with tab1:
        log_action(logger, f'{filename}: tab selected: sample metadata')
        st.header("Sample Metadata")
        query = build_query('sample_metadata', projects, rfids)
        st.code(query) # remove later
        fullquery = 'rollback; begin transaction; ' + query
        df = conn.query(fullquery)
        st.dataframe(df)
        st.write(len(df), ' entries')
        
        csv = convert_df(df)
        
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_sample_metadata_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
    
    # DNA extraction log
    with tab2:
        log_action(logger, f'{filename}: tab selected: DNA extraction')
        st.header("DNA Extraction Log")
        query = build_query('extraction_log', projects, rfids)
        st.code(query) # remove later
        fullquery = 'rollback; begin transaction; ' + query
        df = conn.query(fullquery)
        st.dataframe(df)
        st.write(len(df), ' entries')
    
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_extraction_log_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
    
    # sample barcode library
    with tab3:
        log_action(logger, f'{filename}: tab selected: sample barcode lib')
        st.header("Barcode Library")
    
        runids = st.text_input('find runid', key=3)
        runid =  ', '.join([f"'{v.strip()}'" for v in runids.split(',') if v.strip()])
        pools = st.multiselect(label='select pool', 
                       options=pool, default=None, 
                       placeholder="Choose a pool", disabled=False, label_visibility="visible", key=4)
        pool = ','.join([f"'{v}'" for v in pools])
    
        query = build_query('sample_barcode_lib', projects, rfids, runid, pool)
        st.code(query) # remove later
        fullquery = 'rollback; begin transaction; ' + query
        df = conn.query(fullquery)
        st.dataframe(df)
        st.write(len(df), ' entries')
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_sample_barcode_lib_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    # tissue
    with tab4:
        log_action(logger, f'{filename}: tab selected: tissue')
        st.header("Tissue Received")
    
        query = build_query('tissue', projects, rfids, runid, pool)
        st.code(query) # remove later
        fullquery = 'rollback; begin transaction; ' + query
        df = conn.query(fullquery)
        st.dataframe(df)
        st.write(len(df), ' entries')
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_tissue_received_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    # genotyping log (combine 10.1, 10.2)
    with tab5:
        log_action(logger, f'{filename}: tab selected: genotyping log')
        st.header("Genotyping Logs")
    
        rounds = st.multiselect(label='select round', 
                       options=['10.1', '10.2'], default=None, 
                       placeholder="Choose a genotyping round", disabled=False, label_visibility="visible", key=5)
        round = ','.join([f"'{v}'" for v in rounds])
    
        query = build_query('genotyping_log_total', projects, rfids)
        if round:
            query += f' where pipeline_round in ({round})'
        st.code(query) # remove later
        fullquery = 'rollback; begin transaction; ' + query
        df = conn.query(fullquery)
        st.dataframe(df)
        st.write(len(df), ' entries')
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_genotyping_log_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    # RNA received
    with tab6:
        log_action(logger, f'{filename}: tab selected: RNA received')
        st.header("RNA Received")
    
        query = build_query('rna', projects, rfids)
        st.code(query) # remove later
        fullquery = 'rollback; begin transaction; ' + query
        df = conn.query(fullquery)
        st.dataframe(df)
        st.write(len(df), ' entries')
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_rna_received_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    # RNA Extraction Log
    with tab7:
        log_action(logger, f'{filename}: tab selected: RNA extraction')
        st.header("RNA Extraction Log")
    
        query = build_query('rna_extraction_log', projects, rfids)
        st.code(query) # remove later
        fullquery = 'rollback; begin transaction; ' + query
        df = conn.query(fullquery)
        st.dataframe(df)
        st.write(len(df), ' entries')
    
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_rna_extraction_log_{time.strftime("%Y%m%d")}.csv',
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
    ''')