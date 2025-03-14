"""
This is a tool to get HS West tables from the database.
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

conn = st.connection("palmerdb", type="sql", autocommit=False)
authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')

# for download button
@st.cache_data
def convert_df(df):
    '''IMPORTANT: Cache the conversion to prevent computation on every rerun'''
    return df.to_csv().encode('utf-8')

def reset():
    '''
    clears all cache and streamlit stored data
    '''
    st.session_state.clear()
    st.cache_data.clear()
    rfids = ''
    option = None
    return


st.header('HS West Records')
# st.write("""
         
#          """)

@st.cache_data
def build_query(table=None):
    ''' 
    function that builds an sql query based on user input in 2 fields
    table: tables in schema
    '''
    query = f'SELECT * FROM hs_west_colony.{table}'
    
    if 'drop' in query.lower() or 'commit' in query.lower() \
                                   or 'insert' in query.lower() \
                                   or 'delete' in query.lower() \
                                   or 'update' in query.lower() \
                                   or 'alter' in query.lower()  \
                                   or 'commit' in query.lower():
            st.write("Invalid query.")
            st.stop()
        
    df = conn.query(query)
    st.dataframe(df)
    st.write(df.shape[0], ' samples;', df.shape[1], ' columns')
    return df

if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

if is_logged_in and admin in username:

    st.write('Select a generation and the records to view, or colony for all metadata:')
    gen = None
    table = None
    # table filter by DISPLAY in desc
    tables = conn.query(f"""SELECT table_name
                            FROM information_schema.tables
                            WHERE table_schema = 'hs_west_colony' 
                            AND table_type = 'BASE TABLE';""")
    
    tables = tables.loc[tables.table_name != 'wfu_master']
    display_tables = sorted(tables.table_name.tolist())
    
    gen = st.selectbox(label='Select generation:',
                       options = ['Colony','G101', 'G103'],
                      index=None,
                      placeholder='Choose a generation', disabled=False, label_visibility="visible")
    
    if gen:
        # select table
        table = st.selectbox(label='Select table', 
                       options=[x.split(gen.lower() + '_')[1] for x in display_tables if gen.lower() in x], index=None, 
                       placeholder="Choose an option", disabled=False, label_visibility="visible")
    
    # run query
    if table:
        table = gen.lower() + '_' + table
        df = build_query(table)

        # download
        csv = convert_df(df) 
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'metadata_n{len(df)}_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

# force refresh
if st.button('Refresh', on_click = st.cache_data.clear()):
    log_action(logger, f'{filename}: refresh button clicked')
    st.cache_data.clear()