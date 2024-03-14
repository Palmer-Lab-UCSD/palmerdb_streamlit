"""
# This page is a dashboard for the sample tracking tables in the database.
"""

import streamlit as st
import numpy as np
import pandas as pd
import time
import hmac
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from st_pages import show_pages_from_config, add_indentation, hide_pages
st.set_page_config(
    page_title="Palmer Lab Database Samples",
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

name, authentication_status, username = authenticator.login('main')

# sidebar pages
add_indentation()
if authentication_status == None:
    hide_pages(["Database Summary", "Sample Tracking"])
    st.write('Please login.')
elif authentication_status:
    authenticator.logout('Logout', 'sidebar')
    if st.session_state["name"] == 'palmer':
        show_pages_from_config()
    else:
        hide_pages(["Database Summary", "Sample Tracking"])
        st.write("You do not have permission. Please contact the admin if you think this is a mistake.")
elif authentication_status == False:
    st.error('Username/password is incorrect')

if authentication_status and "admin" in st.session_state["name"]:

    st.title('Palmer Lab Database Samples')
    
    # for download button
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    
    # db connection
    # creds in secret
    conn = st.connection("palmerdb", type="sql", autocommit=False)
    
    # project list
    project = conn.query("select project_name from sample_tracking.project_metadata order by project_name")
    project = project.project_name.tolist()
    # pool list
    pool = conn.query("select distinct pool from sample_tracking.sample_barcode_lib where pool != 'None' order by pool")
    pool = pool.pool.tolist()

    # project selector, rfid filter
    projects = st.multiselect(label='select project', 
                       options=project, default=None, 
                       placeholder="Choose projects", disabled=False, label_visibility="visible", key=1)
    projects = ','.join([f"'{project}'" for project in projects])
    rfids = st.text_input('find rfids', key=2)
    st.write(rfids) # remove later
    rfids =  ', '.join([f"'{v.strip()}'" for v in rfids.split(',') if v.strip()])
    st.write(rfids) # remove later

    def build_query(table, options=None, value=None, value2=None, value3=None):
        ''' 
        function that builds an sql query based on user input in up to 4 fields
        being project, rfid, runid (for barcode), pool (for barcode)
        '''
        conditions = []
    
        if options:
            conditions.append(f"project_name IN ({options})")
    
        if value and value2:
            conditions.append(f"rfid IN ({value}) AND runid = {value2}")
        elif value:
            conditions.append(f"rfid IN ({value})")
        elif value2:
            conditions.append(f"runid = {value2}")
        if value3:
            conditions.append(f"pool IN ({value3})")
            
        query = f"SELECT * FROM sample_tracking.{table}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        return query

    # tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Sample Metadata", "DNA Extraction Log", "Sample Barcodes", 'Tissue Received',
                                                  'Genotyping Logs', 'RNA Received', 'RNA Extraction Log'])

    # sample metadata
    with tab1:
        st.header("Sample Metadata")
        query = build_query('sample_metadata', projects, rfids)
        st.write(query) # remove later
        df = conn.query(query)
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
        st.header("DNA Extraction Log")
        query = build_query('extraction_log', projects, rfids)
        st.write(query) # remove later
        df = conn.query(query)
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
        st.header("Barcode Library")
    
        runids = st.text_input('find runid', key=3)
        runid =  ', '.join([f"'{v.strip()}'" for v in runids.split(',') if v.strip()])
        pools = st.multiselect(label='select pool', 
                       options=pool, default=None, 
                       placeholder="Choose a pool", disabled=False, label_visibility="visible", key=4)
        pool = ','.join([f"'{v}'" for v in pools])
    
        query = build_query('sample_barcode_lib', projects, rfids, runid, pool)
        st.write(query) # remove later
        df = conn.query(query)
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
        st.header("Tissue Received")
    
        query = build_query('tissue', projects, rfids, runid, pool)
        st.write(query) # remove later
        df = conn.query(query)
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
        st.header("Genotyping Logs")
    
        rounds = st.multiselect(label='select round', 
                       options=['10.1', '10.2'], default=None, 
                       placeholder="Choose a genotyping round", disabled=False, label_visibility="visible", key=5)
        round = ','.join([f"'{v}'" for v in rounds])
    
        query = build_query('genotyping_log_total', projects, rfids)
        if round:
            query += f' where pipeline_round in ({round})'
        st.write(query) # remove later
        df = conn.query(query)
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
        st.header("RNA Received")
    
        query = build_query('rna', projects, rfids)
        st.write(query) # remove later
        df = conn.query(query)
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
        st.header("RNA Extraction Log")
    
        query = build_query('rna_extraction_log', projects, rfids)
        st.write(query) # remove later
        df = conn.query(query)
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
        st.cache_data.clear()
