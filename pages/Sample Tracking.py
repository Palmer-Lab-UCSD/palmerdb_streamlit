"""
# This page is a dashboard for the sample tracking tables in the database.
"""
## setup
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
def load_library():
    '''load projects into cache'''
    query = "select distinct library_name from sample_tracking.sample_barcode_lib order by library_name"
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
        if 'drops' in table:
            if 'commit' in value.lower() \
               or 'insert' in value.lower() \
               or 'delete' in value.lower() \
               or 'update' in value.lower() \
               or 'alter' in value.lower()  \
               or 'commit' in value.lower():
                query = 'Invalid query.'
                return query
        else:  
            if 'drop' in value.lower() or 'commit' in value.lower() \
                                       or 'insert' in value.lower() \
                                       or 'delete' in value.lower() \
                                       or 'update' in value.lower() \
                                       or 'alter' in value.lower()  \
                                       or 'commit' in value.lower():
                query = 'Invalid query.'
                return query
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

## start page content
if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

if is_logged_in and admin in username:

    st.title('Palmer Lab Sample Tracking')
    
    # db connection
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
    genotyping_drops = load_table('genotyping_drops')
    error_log = load_table('error_glossary')
    
    # project list
    project = load_projects()
    project = project.project_name.tolist()
    log_action(logger, f'{filename}: project list acquired')
    
    # pool list
    pool = load_pools()
    pool = pool.pool.tolist()
    log_action(logger, f'{filename}: pool list acquired')

    # library list
    library = load_library()
    library = library.library_name.tolist()
    log_action(logger, f'{filename}: library list acquired')

    # project selector, rfid filter
    projects = st.multiselect(label='Select project', 
                       options=project, default=None, 
                       placeholder="Choose projects", disabled=False, label_visibility="visible", key=1) # returns list
    projects_sql = ','.join([f"'{project}'" for project in projects])
    rfids = st.text_input('Find RFIDs', key=2) # returns string
    rfids_sql =  ', '.join([f"'{v.strip()}'" for v in rfids.split(',') if v.strip()])
    
    # tabs
    tab1, tab2, tab3, tab4, tab7, tab8, tab9 = st.tabs(["Sample Metadata", "DNA Extraction Log", "Sample Barcodes", 
                                                        'Tissue Received', 'RNA Received', 'RNA Extraction Log',
                                                        "Known Errors"])
    # sample metadata
    with tab1:
        log_action(logger, f'{filename}: tab selected: sample metadata')
        st.header("Sample Metadata")            
        
        df = filter_df(sample_metadata, projects, rfids)
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
        riptide = st.multiselect(label='Select plate name', 
                       options=library, default=None, 
                       placeholder="Choose a library", 
                       disabled=False, label_visibility="visible", key=6)

        df = filter_df(extraction_log, projects, rfids)
        if riptide:
            df = df.loc[df.riptide_plate_number.isin(riptide)]
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
    
        runids = st.text_input('Select flowcell', key=3)
        runid_sql =  ', '.join([f"'{v.strip()}'" for v in runids.split(',') if v.strip()])
        pools = st.multiselect(label='Select pool', 
                       options=pool, default=None, 
                       placeholder="Choose a pool", disabled=False, label_visibility="visible", key=4)
        pool_sql = ','.join([f"'{v}'" for v in pools])
        riptide = st.multiselect(label='Select plate name', 
                       options=library, default=None, 
                       placeholder="Choose a library", 
                       disabled=False, label_visibility="visible", key=7)
        
        df = filter_df(sample_barcode_lib, projects, rfids, runids, pools)
        if riptide:
            df = df.loc[df.library_name.isin(riptide)]
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
    
    # RNA received
    with tab7:
        log_action(logger, f'{filename}: tab selected: RNA received')
        st.header("RNA Received")
        
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

    # Known Errors
    with tab9:
        log_action(logger, f'{filename}: tab selected: known errors')
        st.header("Known Error Glossary")
        st.write('To search this table, hover over the top right corner of the table and click the magnifying glass.')

        st.dataframe(error_log,hide_index=True,width=900)
        st.write(len(error_log), ' entries')
        
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
        st.markdown("For website support, please contact the Palmer Lab.")
    
    st.image('./assets/Manhattan-Black-Roboto-font-4-alt-5.png')
    st.image('https://palmerlab.org/wp-content/uploads/2019/09/palmerlab-logo.png')