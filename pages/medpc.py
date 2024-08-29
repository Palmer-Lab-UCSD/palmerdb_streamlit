import streamlit as st
import numpy as np
import pandas as pd
from io import StringIO
from components import medpc_extract
from datetime import datetime
from streamlit_cognito_auth import CognitoAuthenticator
from dotenv import load_dotenv
from components.logger import *
from components.authenticate import *
import os
import re
import importlib
from stqdm import stqdm
import yaml
from yaml.loader import SafeLoader
from st_pages import show_pages_from_config, add_indentation, hide_pages
st.set_page_config(
    page_title="Palmer Lab Database Progress Summary",
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


st.title("MedPC Extraction Tool")
st.markdown('''Instructions:

- Upload any number of MedPC files.
- Use the first selector to select relevant measures.
- Use the second selector to select either the first value in the array (total) or the other values (individual bins).
- If total is selected, select "Pivot" to display the data in a compact format.
- If adding or removing files, click the refresh button.
''')

def exp_name_alc(s):
    pattern = re.compile(r'(DAY|DEP)(\w{2})|(\w{1}Q)|(_PR)')
    match = pattern.search(s)
    if match:
        if match.group(1):
            return match.group(1) + match.group(2)
        elif match.group(3):
            return match.group(3)
        elif match.group(4):
            return 'PR'
    return None

def exp_name_george(s):
    pattern = re.compile(r'(PRESHOCK|SHOCK)(\w{2})|(PRESHOCK|SHOCK)|(LGA|SHA|SHOCK|TREATMENT|PR)(\w{2})')
    match = pattern.search(s)
    if match:
        if match.group(1):
            return match.group(1) + match.group(2)
        elif match.group(3):
            return match.group(3)
        elif match.group(4):
            return match.group(4) + match.group(5)
    return None


@st.cache_data
# download button
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')
    
@st.cache_data
def load_files(file):
    stringio = StringIO(file.getvalue().decode("utf-8"))
    string_data = stringio.read()
    dl = string_data.split('\n',1)[0].split('\\')[-1]
    if 'MSN' in string_data.split('\n',1)[1]:
        extract = medpc_extract.read_file(string_data)
    elif 'NumberOfSubjects' in dl:
        extract = medpc_extract.read_file_old_format(string_data)
    return dl, extract

def reset():
    st.session_state.clear()
    st.cache_data.clear()
    return
    

files = st.file_uploader('Upload a MedPC file', type=None, accept_multiple_files=True, label_visibility="visible")
    
if len(files) > 0:
    if 'df' not in st.session_state:
        df = pd.DataFrame()
        status = st.status('file')
        for file in stqdm(files, desc='Processing files'):
            status.update(label=f'{file.name}', state='running')
            dl, extract = load_files(file)
            log_action(logger, f'{filename}: medpc file uploaded; filename: {file.name}')
            extract['file'] = file.name
            df = pd.concat([df, extract])
        status.update(label='', state='complete')
        st.session_state['df'] = df
       
if 'df' in st.session_state:
    df = st.session_state['df']
    df = df.loc[(df['Subject'] != '0') & (~pd.isna(df['Subject']))]
    df.Subject = df.Subject.str.upper()
    measure = df.measure.unique().tolist()
    order = df.order.unique().tolist()
    measures = st.selectbox(label="Choose measure",
                   options=measure, index=0, disabled=False, label_visibility="visible", key=0)
    
    df = df.loc[df.measure == measures]
    log_action(logger, f'{filename}: measures selected {measures}')
        
    if 'ALCOHOL' in df.file.iloc[0] or 'Backup' in df.file.iloc[0]:
        bins = st.selectbox("Choose bins (clear for all)", 
                            ('Total', 'Individual Bins'), index=None, key=1)
        df['name'] = df.file.apply(lambda x: exp_name_alc(x))
    else: 
        bins = None
        df['name'] = df.file.apply(lambda x: exp_name_george(x))
    
    if bins == 'Total':
        df = df.loc[df.order == 0]
        log_action(logger, f'{filename}: bins selected {bins}')
    elif bins == 'Individual Bins':
        df = df.loc[df.order != 0]
        log_action(logger, f'{filename}: bins selected {bins}')


    
    st.dataframe(df, hide_index=True)
    st.write(len(df), 'entries')

    col1, col2 = st.columns(2, gap='small')
    # download
    with col1:
        st.download_button(
                    label="Download data as CSV",
                    data=convert_df(df),
                    file_name=f'extracted_{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.csv',
                    mime='text/csv',
                    )
    
    if bins == 'Total':
        if st.button('Pivot'):
            if 'pivot' in st.session_state:
                del st.session_state['pivot']
            alcohol_exp = ['Subject', 'DAY01', 'DAY02', 'DAY03', 'DAY04', 'DAY05', 'DAY06', 'DAY07', 'DAY08', 'DAY09', 'PR', 'DAY10', '1Q', 'DAY11', '3Q', 'DEP01', 'DEP02', 'DEP03', 'DEP04', 'DEP05', 'DEP06', 'DEP07', 'DEP08', 'DEP09', 'DEP10', 'DEP11', 'DEP12', 'DEPPR', 'DEP13', 'DEP1Q', 'DEP14', 'DEP3Q']
            df['name'] = df.file.apply(lambda x: exp_name_alc(x))
            pivot_df = df.pivot_table(index='Subject', columns='name', values='value',
                                      aggfunc='first').reset_index()
            ordered_exp = [x for x in alcohol_exp if x in pivot_df.columns]
            pivot_df.columns = ordered_exp
            st.dataframe(pivot_df, hide_index = True)
            st.session_state['pivot'] = pivot_df
    
            st.download_button(
                label="Download pivoted data as CSV",
                data=convert_df(st.session_state['pivot']),
                file_name=f'pivoted_extracted_{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.csv',
                mime='text/csv',
                )
        
    else:
        if st.button('Pivot'):
            if 'pivot' in st.session_state:
                del st.session_state['pivot']
            pivot_df = df.pivot_table(index='Subject', columns='name', values='value',
                                      aggfunc='first').reset_index()
            # ordered_exp = [x for x in alcohol_exp if x in pivot_df.columns]
            # pivot_df.columns = ordered_exp
            st.dataframe(pivot_df, hide_index = True)
            st.session_state['pivot'] = pivot_df

            st.download_button(
                label="Download pivoted data as CSV",
                data=convert_df(st.session_state['pivot']),
                file_name=f'pivoted_extracted_{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.csv',
                mime='text/csv',
                )

    # refresh
    with col2:
        if st.button('Refresh', on_click = st.cache_data.clear()):
            log_action(logger, f'{filename}: refresh button')
            st.cache_data.clear()
            st.session_state.clear()
            st.rerun()


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
    
    st.image('./assets/GWAS_1200x150pxBanner-01.png')
    st.image('https://palmerlab.org/wp-content/uploads/2019/09/palmerlab-logo.png')