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
    
# cached functions
@st.cache_resource
def init_connection():
    return st.connection("palmerdb", type="sql", autocommit=False)

@st.cache_data
def convert_df(df):

    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

@st.cache_data(ttl=1800)
def load_table(table_name):
    '''load table into cache'''
    query = f"select * from sample_tracking.{table_name}"
    df = conn.query(query)
    return df

@st.cache_data
def load_pools():
    '''load pools into cache'''
    query = "select distinct pool from sample_tracking.sample_barcode_lib where pool != 'None' order by pool"
    df = conn.query(query)
    return df

@st.cache_data
def load_projects():
    '''load projects into cache'''
    query = "select project_name from sample_tracking.project_metadata order by project_name"
    df = conn.query(query)
    return df

@st.cache_data
def filter_df(df, projects=None, rfids=None, runids=None, pools=None):
    '''
    filter the cached table
    all inputs other than df must be list
    '''
    if projects:
        df = df.loc[df.project_name.isin(projects)]
    if rfids:
        df = df.loc[df.rfid.isin(rfids.split(', '))]
    if runids:
        df = df.loc[df.runid.isin(runids.split(', '))]
    if pools:
        df = df.loc[df.pool.isin(pools)]
    return df

@st.cache_data
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
    
    if 'drop' in query.lower() or 'commit' in query.lower() \
                                   or 'insert' in query.lower() \
                                   or 'delete' in query.lower() \
                                   or 'update' in query.lower() \
                                   or 'alter' in query.lower()  \
                                   or 'commit' in query.lower():
            st.write("Invalid query.")
            st.stop()
            
    return query

if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

if is_logged_in and admin in username:

    st.title('Palmer Lab Sample Tracking')
    
    # db connection
    # conn = st.connection("palmerdb", type="sql", autocommit=False)
    conn = init_connection()
    log_action(logger, f'{filename}: db connection made')

    
    # load tables
    sample_metadata = load_table('sample_metadata')
    extraction_log = load_table('extraction_log')
    sample_barcode_lib = load_table('sample_barcode_lib')
    tissue = load_table('tissue')
    rna = load_table('rna')
    rna_extraction_log = load_table('rna_extraction_log')
    genotyping_log = load_table('genotyping_log_total')
    rna = load_table('rna')
    rna_extraction_log = load_table('rna_extraction_log')
    
    # project list
    project = load_projects()
    project = project.project_name.tolist()
    log_action(logger, f'{filename}: project list acquired')
    
    # pool list
    pool = load_pools()
    pool = pool.pool.tolist()
    log_action(logger, f'{filename}: pool list acquired')

    # project selector, rfid filter
    projects = st.multiselect(label='Select project', 
                       options=project, default=None, 
                       placeholder="Choose projects", disabled=False, label_visibility="visible", key=1) # returns list
    projects_sql = ','.join([f"'{project}'" for project in projects])
    rfids = st.text_input('Find RFIDs', key=2) # returns string
    rfids_sql =  ', '.join([f"'{v.strip()}'" for v in rfids.split(',') if v.strip()])
    
    # tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Sample Metadata", "DNA Extraction Log", "Sample Barcodes", 
                                                        'Tissue Received', 'Genotyping Logs', 'Genotyping Drops','RNA Received', 'RNA Extraction Log'])
    # sample metadata
    with tab1:
        log_action(logger, f'{filename}: tab selected: sample metadata')
        st.header("Sample Metadata")
        query = build_query('sample_metadata', projects_sql, rfids)
        st.code(query) # remove later
        
        df = filter_df(sample_metadata, projects, rfids)
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        st.dataframe(df, hide_index=True)
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
        query = build_query('extraction_log', projects_sql, rfids_sql)
        st.code(query) # remove later
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        
        df = filter_df(extraction_log, projects, rfids)
        st.dataframe(df, hide_index=True)
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
        runid_sql =  ', '.join([f"'{v.strip()}'" for v in runids.split(',') if v.strip()])
        pools = st.multiselect(label='select pool', 
                       options=pool, default=None, 
                       placeholder="Choose a pool", disabled=False, label_visibility="visible", key=4)
        pool_sql = ','.join([f"'{v}'" for v in pools])
    
        query = build_query('sample_barcode_lib', projects_sql, rfids_sql, runid_sql, pool_sql)
        st.code(query) # remove later
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        
        df = filter_df(sample_barcode_lib, projects, rfids, runids, pools)
        st.dataframe(df, hide_index=True)
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
    
        query = build_query('tissue', projects_sql, rfids_sql)
        st.code(query) # remove later
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        
        df = filter_df(tissue, projects, rfids)
        st.dataframe(df, hide_index=True)
        st.write(len(df), ' entries')
        
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_tissue_received_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    # genotyping log (combined)
    with tab5:
        log_action(logger, f'{filename}: tab selected: genotyping log')
        st.header("Genotyping Logs")
        pipeline_ver = conn.query("select distinct pipeline_round from sample_tracking.genotyping_log_total\
                                    order by pipeline_round")
        pipe_round = st.multiselect(label='select round', 
                       options=pipeline_ver, default=None, 
                       placeholder="Choose a genotyping round", disabled=False, label_visibility="visible", key=5)
        round_sql = ','.join([f"'{v}'" for v in pipe_round])
        
        if "'p50_hao_chen'" in projects_sql:
            projects_sql = projects_sql.replace("'p50_hao_chen'", "'p50_hao_chen_2020', 'p50_hao_chen_2014'")
            projects = [item if item != 'p50_hao_chen' else 'p50_hao_chen_2020' for item in projects]
            projects.insert(projects.index('p50_hao_chen_2020') + 1, 'p50_hao_chen_2014')

    
        query = build_query('genotyping_log_total', projects_sql, rfids_sql)
        if pipe_round:
            if "WHERE" in query.upper():
                query += f' and pipeline_round in ({round_sql})'
            else:
                query += f' where pipeline_round in ({round_sql})'
        st.code(query) # remove later
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        
        df = filter_df(genotyping_log, projects, rfids)
        if pipe_round:
            df = df.loc[df.pipeline_round.isin(pipe_round)]

        st.dataframe(df, hide_index=True)
        st.write(len(df), ' entries')
        
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_genotyping_log_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
        
    # genotyping drops
    with tab6:
        log_action(logger, f'{filename}: tab selected: genotyping drops')
        st.header("Genotyping Drops")
    
        query = build_query('genotyping_drops', projects_sql, rfids_sql)
        st.code(query) # remove later
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        
        df = filter_df(genotyping_log, projects, rfids)

        st.dataframe(df, hide_index=True)
        st.write(len(df), ' entries')
        
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_genotyping_drops_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    # RNA received
    with tab7:
        log_action(logger, f'{filename}: tab selected: RNA received')
        st.header("RNA Received")
    
        query = build_query('rna', projects_sql, rfids_sql)
        st.code(query) # remove later
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        
        df = filter_df(rna, projects, rfids)
        st.dataframe(df, hide_index=True)
        st.write(len(df), ' entries')
        
        csv = convert_df(df)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'n{len(df)}_rna_received_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    # RNA Extraction Log
    with tab8:
        log_action(logger, f'{filename}: tab selected: RNA extraction')
        st.header("RNA Extraction Log")
    
        query = build_query('rna_extraction_log', projects_sql, rfids_sql)
        st.code(query) # remove later
        # fullquery = 'rollback; begin transaction; ' + query
        # df = conn.query(fullquery)
        
        df = filter_df(rna_extraction_log, projects, rfids)
        st.dataframe(df, hide_index=True)
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
    
    Palmer Lab IRS
    ''')
    with st.container(border=True):
        st.write('##### :green[Support]')
        st.markdown("For website support, please contact the Palmer Lab, or Elaine directly at ekeung@health.ucsd.edu.")
    
    st.image('./assets/Manhattan-Black-Roboto-font-4-alt-5.png')
    st.image('https://palmerlab.org/wp-content/uploads/2019/09/palmerlab-logo.png')