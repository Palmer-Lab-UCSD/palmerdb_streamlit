"""
This is a tool to get metadata from the database given RFIDs.
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



st.header('Rat Metadata')
st.markdown("""This page will return the Palmer Lab's metadata records for rats based on their RFID.

To use, paste a list of RFIDs in the text box. RFIDs can be separated by newlines, commas, or spaces, but should not include quotes or any other character.""")

if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
    # query projects
    projects = conn.query("select distinct project_name from sample_tracking.sample_metadata order by project_name")
    projects = sorted(projects.project_name.tolist())

    if admin in username:
        # should only be available to palmer
        option = st.selectbox(label='Select project', 
                           options=projects, index=None, 
                           placeholder="Choose an option", disabled=False, label_visibility="visible")
    else: option = None

    # start processing rfids
    rfids = ''
    rfids = st.text_area(label='Enter RFIDs:', value='')
    if len(rfids) >= 1:
        if ',' in rfids:
            # if they are comma separated
            rfids =  ', '.join([f"'{v.strip()}'" for v in rfids.split(',') if v.strip()])
        else:
            # if they are not comma separated
            rfids =  ', '.join([f"'{v.strip()}'" for v in rfids.split() if v.strip()])
        st.write(rfids)


    # # file uploader
    # # file should only contain rfids
    # # (or rfid is first column)
    # # must be csv
    # file = st.file_uploader('Upload a CSV containing a list of RFIDs:', type=['csv'], 
    #                         accept_multiple_files=False, label_visibility="visible", 
    #                         help='''The CSV contents should only contain RFIDs, e.g "rfid1, rfid2, rfid3..." each on a new line.
    #                         There should not be any column headers.''')

    # # if a file was uploaded, processs the rfids
    # if file is not None:
    #     df = pd.read_csv(file, header=None, dtype=str)
    #     rfids = ','.join([f"'{v.strip()}'" for v in df[0].tolist() if v.strip()])



    def build_query(project=None, rfid=None):
        ''' 
        function that builds an sql query based on user input in 2 fields
        project: list of projects
        rfid: list of rfids
        '''

        if project:
            query = f'SELECT * FROM {project}.wfu_master '
        else:
            query = f"SELECT project_name FROM sample_tracking.sample_metadata "

        if rfid:
            log_action(logger,  f'{filename}: rfids selected: {rfid}')
            query += f"WHERE rfid IN ({rfid})"

        df = conn.query(query)

        # from individual rfids (don't know project)
        if 'sample_metadata' in query:
            queries = []
            temp = conn.query(query)
            proj = temp.project_name.unique().tolist()
            for project in proj:
                query = f"""
                        SELECT *, '{project}' as project_name
                        FROM {project}.wfu_master
                        WHERE rfid in ({rfid})
                        """
                queries.append(query)
            df = pd.DataFrame()
            for query in queries:
                df = pd.concat([df, conn.query(query)]) 

        return df

    # only run query if input
    if option is not None or len(rfids) >= 1:
        df = build_query(option, rfids)
        st.dataframe(df)

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
        
else: st.write('Please sign in to use.')