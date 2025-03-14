"""
This is a tool to get tables from the database with permissions.
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


st.header('Database Records')
st.write("""
         Please sign in to view individual tables from the Palmer Lab Database for your projects.  
         To request additional permissions, please contact the Palmer Lab.
         """)

def build_query(project=None, table=None):
    ''' 
    function that builds an sql query based on user input in 2 fields
    project: list of projects
    table: tables in schema
    '''
    query = f'SELECT * FROM {project}.{table}'
    if 'drop' in query.lower() or 'commit' in query.lower() \
                                   or 'insert' in query.lower() \
                                   or 'delete' in query.lower() \
                                   or 'update' in query.lower() \
                                   or 'alter' in query.lower()  \
                                   or 'commit' in query.lower():
            st.write("Invalid query.")
            st.stop()
            
    df = conn.query(query)
    return df

if is_logged_in and admin not in username:
    # case: logged in, external account
    prefix = username.split('_')[0]
    perm = conn.query(f"""select * from sample_tracking.irs_permissions where username like '{prefix}'""")
elif is_logged_in and admin in username:
    # case: logged in, admin
    perm = conn.query(f"""select distinct project_name as projects 
                          from sample_tracking.project_metadata 
                          order by project_name""")
else:
    # case: not logged in
    perm = None
    
if perm is not None and perm.projects[0] is not None:
    # project list available
    if admin not in username:
        allow = perm.projects[0].split(', ')
    else: 
        allow = perm.projects.tolist()
        
    st.write('''Use the dropdowns to select the table you'd like to retrieve.  
    The table is interactive:
- Click on a column to sort the table by that column.
- Hover in the top right of the table to find a search option or to enter fullscreen.''')
    st.write('*Note: Due to the size of some tables, the query may take a while, and the displayed data will be truncated. The full data is available for download using the button at the bottom of the page.*')

    # query projects
    projects = sorted([x for x in allow if 'hs_west_colony' not in x])

    # project picker
    option = st.selectbox(label='Select project', 
                       options=projects, index=None, 
                       placeholder="Choose an option", disabled=False, label_visibility="visible")

    # table filter by DISPLAY in desc
    tables = conn.query(f"""SELECT c.relname AS table_name, d.description
                            FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            LEFT JOIN pg_description d ON c.oid = d.objoid
                            WHERE c.relkind = 'r'  -- 'r' means regular table
                            AND n.nspname = '{option}'  -- replace with your schema name
                            AND d.description LIKE '%DISPLAY%';""")

    # legible names
    table_map = {
        'behavioral':'behavioral phenotypes',
        'nicsa':'nicsa phenotypes',
        'raw_phenotypes':'raw data',
        'gwas_phenotypes_current':'behavioral phenotypes',
        'gwas_phenotypes':'behavioral phenotypes',
        'locomotor_phenotypes':'locomotor phenotypes',
        'runway_phenotypes':'runway phenotypes',
        'progressiveratio_phenotypes':'progressive ratio phenotypes',
        'progressivepunishment_phenotypes':'progressive punishment phenotypes',
        'dissection':'physiological phenotypes',
        'physio_phenotypes':'physiological phenotypes',
        'wfu_master_corrected':'sample metadata',
        'wfu_master':'sample metadata',
        'ucsf_master':'sample metadata',
        'ucsd_master':'sample metadata',
        'colony_master':'colony metadata',
        'descriptions':'trait descriptions'
    }
    tm = {k: v for k, v in table_map.items() if k in tables['table_name'].values}
    
    display_tables = tables.table_name.map(tm).tolist()

    # select table
    select_table = st.selectbox(label='Select data', 
                       options=display_tables, index=None, 
                       placeholder="Choose an option", disabled=False, label_visibility="visible")

    # re-map names
    if select_table:
        table = [key for key, value in tm.items() if value == select_table][0]
    else: table = None
    
    # run query
    if option and table:
        run = st.button('Run query')
        if run:
            df = build_query(option, table)
            if df.shape[0] > 500:
                st.write('Due to the large size of the data, only the first 200 rows will be shown. The remaining rows will exist in the downloaded CSV (button below).')
            st.dataframe(df.head(200))
            st.write(df.shape[0], ' samples;', df.shape[1], ' columns')

            # download
            csv = convert_df(df) 
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'{option}_{table}_n{len(df)}_{time.strftime("%Y%m%d")}.csv',
                mime='text/csv',
            )

# force refresh
if st.button('Refresh', on_click = st.cache_data.clear()):
    log_action(logger, f'{filename}: refresh button clicked')
    st.cache_data.clear()