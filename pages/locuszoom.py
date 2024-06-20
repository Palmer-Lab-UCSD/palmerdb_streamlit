"""
# This page is an template for the GWAS reports.
"""

import streamlit as st
import numpy as np
import pandas as pd
from components.logger import *
from components.authenticate import *
import os
from streamlit_cognito_auth import CognitoAuthenticator
from dotenv import load_dotenv
from st_pages import show_pages_from_config, add_indentation, hide_pages
import streamlit.components.v1 as components
import time
import wget
from zipfile import ZipFile 
from GWAS_pipeline.gwas_class_auto import *

st.set_page_config(
    page_title="Palmer Lab Database",
    page_icon="🐀",
    layout="wide",
    initial_sidebar_state="auto"
)
logger = setup_logger()
filename = os.path.basename(__file__)

log_action(logger, f'{filename}: page opened')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
else:
    st.write('Please sign in.')

# if is_logged_in:

@st.experimental_fragment
def phewas(self):
    self.phewas_widget()
    return

@st.experimental_fragment
def locuszoom(self):
    self.locuszoom_widget()
    return

def reset():
    if 'gwas' in st.session_state:
        del st.session_state['gwas']

st.header('GWAS Tools')
st.write('''Please use the following tools to customize Phenotype Wide Association Study (PheWAS) tables and Regional Association Plots (Locuszoom) for your projects.''')

with st.expander('###### :green[Usage Notes and Tips]', expanded=True):
    st.write('''
- **Most processes on this page take several minutes to run as they are more computationally intensive.**
    - After editing any custom values, please allow a few (1-3) seconds before clicking another widget. Tools may break if customizable values are changed in rapid succession.
- Please select the project and the version of the GWAS report containing the data to use.
- The page will download and unzip the appropriate files; this can take several minutes.
- The PheWAS and Plot tools should load in once the data is prepared. 
- To use the tools, fill in the parameters in the dropdowns, and click the "Run" button.
- The program uses the rn7 gene list from NCBI RefSeq from NCBI GTF.
- In case of errors or extremely poor performance, it is recommended to refresh the webpage to fully reset.''')


# # prepare reading files
# files_df = pd.read_csv()
# files_df = files_df.loc[files_df.project_name.str.contains(username[:-3])]
# project_list = files_df.project_name.unique().tolist()    

# # input project and filter
# project = st.selectbox(label='Projects', options=project_list, placeholder='Pick a project:', index=None)
# files_df = files_df.loc[files_df.project_name == project]
# filelist = sorted(files_df.filename.unique().tolist(), reverse=True)
# filelist[0] = 'LATEST: ' + filelist[0] 

# # input file
# file = st.selectbox(label='Report Files:', options=filelist, placeholder='Pick a report file:')

# manual, for later deletion
project = st.text_input(label='Project', placeholder='Enter project name', on_change=reset)
file = st.text_input(label='Filename', placeholder='Enter file name', on_change=reset)

if 'gwas' not in st.session_state:
    downloaded = ['run_u01_olivier_george_cocaine_tsanches_10.2.1_v0.2.0-17-g646a544.zip']
    if len(file) > 1 and len(project) > 1:
        url = f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{project}/{file}'
        with st.status("Initializing...") as status:
            status.update(label="Downloading data...", state="running")
            if file not in downloaded:
                filename = wget.download(url)
                downloaded += file
                with ZipFile(f"{filename}", 'r') as zObject:
                    status.update(label="Download complete.", state="complete")
                    time.sleep(3)
                    status.update(label="Unzipping data...", state='running')
                    zObject.extractall() 
            else:
                filename = downloaded[-1]
                status.update(label='Ready!', state='complete')
    else:
        st.stop()
        
    df = pd.read_csv(f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{project}/processed_data_ready.csv', dtype = {'rfid':str})
    gwas = gwas_pipe(path = f'./tscc/projects/ps-palmer/gwas/projects/{project}/',
                 data = df,
                 project_name = f'{project}',
                 n_autosome =20,
                 all_genotypes =  f'./tscc/projects/ps-palmer/gwas/projects/{project}/genotypes/genotypes',
                 traits = [], 
                 threshold=5.36,
                 founderfile = '/founder_genotypes/founders7.2',
                 locuszoom_path='/GWAS_pipeline/locuszoom/',
                 phewas_db = 'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/phewasdb_rn7_g102.parquet.gz',
                 threads = 6,
                 gtf = f'./GWAS_pipeline/rn_7_gtf.csv')
    self = gwas
    st.session_state['gwas'] = self
    

if 'gwas' in st.session_state:
    self = st.session_state['gwas']
    st.write('##### Phenotype Wide Association Study (PheWAS): ')
    phewas(self)
    st.write('##### Locuszoom Plot: ')
    locuszoom(self)
    # self.phewas_widget()
    # self.locuszoom_widget()
    # self.locuszoom_interactive()
    
    if st.button("Refresh"):
        reset()
        st.rerun()
