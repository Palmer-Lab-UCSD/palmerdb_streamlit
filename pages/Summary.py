"""
# This page is an overview for the numbers in the database.
"""

import streamlit as st
import numpy as np
import pandas as pd
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
    st.write('Please sign in.')
    hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary", "Genotyping Metadata"])
elif is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
    def logout():
        authenticator.logout()
    with st.sidebar:
        st.write(f"Welcome, {authenticator.get_username()}!")
        st.button("Logout", "logout_btn", on_click=logout)
    if admin not in username:
        st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')
        hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary", "Genotyping Metadata"])


if is_logged_in and admin in username:
    # db connection
    # creds in secret
    conn = st.connection("palmerdb", type="sql", autocommit=False)
    log_action(logger, f'{filename}: db connection made')
    
    # project list
    project = conn.query("select distinct project_name from sample_tracking.project_metadata order by project_name")
    project = project.project_name.tolist()
    log_action(logger, f'{filename}: project list acquired')
    
    st.title('Palmer Lab Database Summary')
    
    # for download button
    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')
    
    options = st.multiselect(label='select project', 
                   options=project, default=None, 
                   placeholder="Choose an option", disabled=False, label_visibility="visible")
    # options = ','.join([f"'{option}'" for option in options])

    # query text
    sql = '''
        rollback;
        begin transaction;
           with tissue as 
                    (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS tissue
                    FROM sample_tracking.sample_metadata sm
                    JOIN sample_tracking.tissue gl ON sm.rfid = gl.rfid
                    GROUP BY sm.project_name),
           dna as 
                   (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS dna_extracted
                    FROM sample_tracking.sample_metadata sm
                    JOIN sample_tracking.extraction_log gl ON sm.rfid = gl.rfid
                    GROUP BY sm.project_name),
           sequenced as 
                   (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS sequenced
                    FROM sample_tracking.sample_metadata sm
                    JOIN sample_tracking.sample_barcode_lib gl ON sm.rfid = gl.rfid
                    GROUP BY sm.project_name),
           genotype as 
                   (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS genotyped
                    FROM  sample_tracking.sample_metadata sm
                    JOIN sample_tracking.genotyping_log_total gl ON sm.rfid = gl.rfid
                    GROUP BY sm.project_name),
           redo AS 
        		(SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS redo
        		FROM sample_tracking.sample_metadata sm
        		JOIN sample_tracking.genotyping_log_total gl ON sm.rfid = gl.rfid
        		WHERE gl.sample_use LIKE 're%'
        		GROUP BY sm.project_name),
           ship as (select project_name, count(project_name) as shipped from sample_tracking.sample_metadata group by project_name),
           rna as 
                    (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS rna_sent
                    FROM sample_tracking.sample_metadata sm
                    JOIN sample_tracking.rna gl ON sm.rfid = gl.rfid
                    GROUP BY sm.project_name),
           rna_extract as 
                   (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS rna_extracted
                    FROM sample_tracking.sample_metadata sm
                    JOIN sample_tracking.rna_extraction_log gl ON sm.rfid = gl.rfid
                    GROUP BY sm.project_name)
    
    
            SELECT 
                distinct pm.project_name, 
                coalesce(h.shipped, 0) as shipped,
                COALESCE(t.tissue, 0) AS tissue, 
                COALESCE(d.dna_extracted, 0) AS dna_extracted, 
                COALESCE(s.sequenced, 0) AS sequenced, 
                COALESCE(g.genotyped, 0) AS genotyped,
                COALESCE(r.redo, 0) AS redo,
                COALESCE(rna.rna_sent, 0) AS rna_received,
                COALESCE(rne.rna_extracted, 0) AS rna_extracted
            FROM 
                sample_tracking.project_metadata pm
            LEFT JOIN tissue t ON pm.project_name = t.project_name
            LEFT JOIN dna d ON pm.project_name = d.project_name
            LEFT JOIN sequenced s ON pm.project_name = s.project_name
            LEFT JOIN genotype g ON pm.project_name = g.project_name
            LEFT JOIN redo r ON pm.project_name = r.project_name
            left join ship h on pm.project_name = h.project_name
            left join rna rna on pm.project_name = rna.project_name
            left join rna_extract rne on pm.project_name = rne.project_name
    
            order by pm.project_name
    '''
    # make connection
    df = conn.query(sql)
    log_action(logger, f'{filename}: form dataframe')

    # filter selected projects
    if len(options) > 0:
        log_action(logger, f'{filename}: filter dataframe')
        df = df.loc[df.project_name.isin(options)]
        
    # display df, shape
    st.dataframe(df)
    
    st.write(len(df), ' projects')

    # download
    csv = convert_df(df) 
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name=f'n{len(df)}_{time.strftime("%Y%m%d")}.csv',
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