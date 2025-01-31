"""
# This page is for the GWAS reports.
"""

import streamlit as st
import numpy as np
import pandas as pd
from IPython.display import IFrame, display, HTML
import streamlit.components.v1 as components
from components.logger import *
from components.authenticate import *
import os
import time
import string
import re
from streamlit_cognito_auth import CognitoAuthenticator
from dotenv import load_dotenv
from st_pages import show_pages_from_config, add_indentation, hide_pages
st.set_page_config(
    page_title="Palmer Lab Database",
    page_icon="🐀",
    layout="wide",
    initial_sidebar_state="auto"
)

conn = st.connection("palmerdb", type="sql", autocommit=False)
logger = setup_logger()
filename = os.path.basename(__file__)
log_action(logger, f'{filename}: page entered')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')

def extract_n(input_string):
    match = re.search(r'n\d+_', input_string)
    if match:
        return match.group(0)[:-1]
    else:
        return 'UNK'
    
def extract_date(input_string):
    match = re.search(r'\d{4}-\d{2}-\d{2}', input_string)
    if match:
        return match.group(0)
    else:
        return 'UNK'

st.title('GWAS Reports')
st.write('Please sign in to access an archive of GWAS reports for your projects.')
    
data = 'https://www.dropbox.com/scl/fi/wrhelbhblbqp294epvbyg/gwas_reports.csv?rlkey=byxwurl53dvdenkywv8r4rvpe&dl=1'

if is_logged_in:
    # df = pd.read_csv(data)
    df = conn.query(f"""select * from sample_tracking.gwas_reports""")
    
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

    # query projects
    reports = df.project.unique()
    allow = [x for x in allow if x in reports]
    projects = sorted(allow)

    # project picker
    option = st.selectbox(label='Select project', 
                       options=projects, index=None, 
                       placeholder="Choose an option", disabled=False, label_visibility="visible")

    # b = st.selectbox(label='Select a project:', options=sorted(df.project.unique()), index=None, placeholder='Project name')
    if option is not None:
        log_action(logger, f'{filename}: selected project {option}')
        df2 = df.loc[df.project == option]

        a = list(zip(df2['samples'].tolist(), df2['date'].tolist()))
        a = sorted(a, key=lambda x: x[1], reverse=True)
        a = [f"samples = {n}, date = {date}" for n, date in a]
        a[0] = a[0] + ' [LATEST]'

        c = st.selectbox(label='Select a report to view:', options=a, index=None, placeholder='number of samples, date of GWAS')

        if c is not None:
            log_action(logger, f'{filename}: selected report {c}')
            selected_n = re.search(r'n\d+,', c).group(0)[:-1]
            selected_date = extract_date(c)

            report = df.loc[(df.samples == selected_n) & (df.date == selected_date), 'path'].iloc[0]
            st.markdown(f'[Click here to view report as full webpage.]({report})')

            # display
            components.iframe(report, width=None, height=800, scrolling=True)
            
            
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