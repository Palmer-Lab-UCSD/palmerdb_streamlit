"""
# This page is for the locuszoom and phewas.
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
import shutil
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
    files = os.listdir('.')
    zip_files = [file for file in files if file.endswith('.zip')]
    if len(zip_files) > 3:
        for file in zip_files[:-1]:
            os.remove(file)
        if os.path.exists('tscc') and os.path.isdir('tscc'):
            shutil.rmtree('tscc')

st.header('GWAS Tools')
st.write('''The following tools can be used to customize Phenotype Wide Association Study (PheWAS) tables and Regional Association Plots (Locuszoom) for your projects.''')

with st.expander('###### :green[Usage Notes and Tips]', expanded=True):
    st.write('''
- **Most processes on this page take several minutes to run as they are more computationally intensive.**
    - After editing any custom values, please allow a few (1-3) seconds before clicking another widget. Tools may break if customizable values are changed in rapid succession.
- Please sign in to view projects.
- Please select the project and the version of the GWAS report containing the data to use.
- The page will download and unzip the appropriate files; this can take several minutes.
- The PheWAS and Plot tools should load in once the data is prepared. 
- To use the tools, fill in the parameters in the dropdowns, and click the "Run" button.
- The program uses the rn7 gene list from NCBI RefSeq from NCBI GTF.
- In case of errors or extremely poor performance, it is recommended to refresh the webpage to fully reset.''')
    

if is_logged_in:
    # prepare reading files
    files_df = pd.read_csv('https://www.dropbox.com/scl/fi/k24hv7jclwxkz6qjf4pdh/gwas_files.csv?rlkey=yb7k00dzli0874dc64fplgt6w&dl=1')
    if admin not in username:
        files_df = files_df.loc[files_df.project.str.contains(username.split('_')[0])]
    project_list = sorted(files_df.project.unique().tolist())    

    # input project and filter
    project = st.selectbox(label='Projects', options=project_list, placeholder='Pick a project:', index=None, on_change=reset())
    if project is not None:
        files_df = files_df.loc[files_df.project == project].sort_values(by='modified', ascending=False)
        filelist = files_df.file.str.split('/').str[-1].unique().tolist()
        filelist[0] = '[LATEST] ' + filelist[0]

        # input file
        file = st.selectbox(label='Report Files:', options=filelist, placeholder='Pick a report file:', index=None, on_change=reset())
        if file is not None and 'LATEST' in file:
            file = file[9:]

        if 'gwas' not in st.session_state:
            if file is not None and project is not None:
                url = f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{project}/{file}'
                with st.status("Initializing...") as status:
                    status.update(label="Downloading data...", state="running")
                    if os.path.isfile(file):
                        with ZipFile(f"{file}", 'r') as zObject:
                            status.update(label="Unzipping data...", state='running')
                            zObject.extractall() 
                            status.update(label='Ready!', state='complete')
                    else:
                        filename = wget.download(url)
                        with ZipFile(f"{filename}", 'r') as zObject:
                            status.update(label="Download complete.", state="complete")
                            time.sleep(3)
                            status.update(label="Unzipping data...", state='running')
                            zObject.extractall() 
                    
            else:
                st.stop()

            df = pd.read_csv(f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{project}/processed_data_ready.csv', dtype = {'rfid':str})
            
            # edge
            if os.path.isdir(f'./tscc/projects/ps-palmer/gwas/projects/{project}/'):
                path = f'./tscc/projects/ps-palmer/gwas/projects/{project}/'
            else:
                path = f'./{project}'
                
            # init
            gwas = gwas_pipe(path = path,
                         data = df,
                         project_name = f'{project}',
                         n_autosome =20,
                         all_genotypes =  path + '/genotypes/genotypes',
                         traits = [], 
                         threshold=5.36,
                         founderfile = '/founder_genotypes/founders7.2',
                         locuszoom_path='/GWAS_pipeline/locuszoom/',
                         phewas_db = 'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/phewasdb_rn7_g102.parquet.gz',
                         threads = 6,
                         gtf = f'https://www.dropbox.com/scl/fi/ai1fw6fxsazns0pt40yec/rn_7_gtf.csv?rlkey=ovyi0mdaz71oci9mhtxchhvxw&dl=1')
            self = gwas
            st.session_state['gwas'] = self


        if 'gwas' in st.session_state:
            self = st.session_state['gwas']
            st.write('##### Phenotype Wide Association Study (PheWAS): ')
            phewas(self)
            st.write('##### Locuszoom Plot: ')
            locuszoom(self)

            if st.button("Refresh"):
                # hard clear
                reset()
                st.rerun()
                
