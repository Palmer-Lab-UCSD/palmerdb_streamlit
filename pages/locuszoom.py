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
conn = st.connection("palmerdb", type="sql", autocommit=False)
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
    # do not store more than 3 zip files
    if 'gwas' in st.session_state:
        del st.session_state['gwas']
    files = os.listdir('.')
    zip_files = [file for file in files if file.endswith('.zip')]
    if len(zip_files) > 2:
        for file in zip_files[:-1]:
            os.remove(file)
        if os.path.exists('tscc') and os.path.isdir('tscc'):
            shutil.rmtree('tscc')
        if os.path.exists('projects') and os.path.isdir('projects'):
            shutil.rmtree('projects')

st.header('GWAS Tools')
st.write('''The following tools can be used to customize Phenotype Wide Association Study (PheWAS) tables and Regional Association Plots (Locuszoom) for your projects.

Please sign in to view available projects.
''')

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
    
files_df = pd.read_csv('https://www.dropbox.com/scl/fi/k24hv7jclwxkz6qjf4pdh/gwas_files.csv?rlkey=yb7k00dzli0874dc64fplgt6w&dl=1')

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
    reports = files_df.project.unique()
    allow = [x for x in allow if x in reports or 'hao_chen' in x]
    projects = sorted(allow)
    
    # project picker
    project = st.selectbox(label='Select project', 
                       options=projects, index=None, 
                       placeholder="Choose an option", disabled=False, label_visibility="visible")


    if project is not None:
        # edge cases
        if 'hao_chen' in project:
            project = st.selectbox(label='Select project', 
                       options=['p50_hao_chen_2020','p50_hao_chen_novel', 'p50_hao_chen_social'], 
                       placeholder="Choose an option", disabled=False, label_visibility="visible")
        elif 'alcohol' in project: project = 'r01_deguglielmo_etoh'
        
        # add latest tag
        log_action(logger, f'{filename}: selected project {project}')
        files_df = files_df.loc[files_df.project == project].sort_values(by='modified', ascending=False)
        filelist = files_df.file.str.split('/').str[-1].unique().tolist()
        filelist[0] = '[LATEST] ' + filelist[0]

        # input file
        file = st.selectbox(label='Report Files:', options=filelist, placeholder='Pick a report file:', index=None, on_change=reset())
        if file is not None and 'LATEST' in file:
            log_action(logger, f'{filename}: selected file {file}')
            file = file[9:]

        # begin init
        if 'gwas' not in st.session_state:
            if file is not None and project is not None:
                # get data
                url = f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{project}/{file}'
                with st.status("Initializing...") as status:
                    status.update(label="Preparing data...", state="running")
                    try:
                        if os.path.isfile(file):
                            # if already have zip
                            log_action(logger, f'{filename}: already have {url} unzipping')
                            with ZipFile(f"{file}", 'r') as zObject:
                                status.update(label="Loading data...", state='running')
                                zObject.extractall() 
                                status.update(label='Ready! Initializing object.', state='complete')
                        else:
                            # if do not have zip
                            filename = wget.download(url)
                            log_action(logger, f'{filename}: getting {url}')
                            with ZipFile(f"{filename}", 'r') as zObject:
                                status.update(label="Data preparation complete.", state="complete")
                                time.sleep(3)
                                status.update(label="Loading data...", state='running')
                                zObject.extractall()
                                status.update(label="Ready! Initializing object.", state='complete')
                                
                    # volume space issues
                    # dir structure from extract includes /tscc, /project commonly
                    # also remove all zip files
                    except OSError as e:
                        if 'space' in str(e):
                            st.write('Clearing storage...')
                            files = os.listdir('.')
                            zip_files = [file for file in files if file.endswith('.zip')]
                            for file in zip_files:
                                os.remove(file)
                            if os.path.exists('tscc') and os.path.isdir('tscc'):
                                shutil.rmtree('tscc')
                            if os.path.exists(project) and os.path.isdir(project):
                                shutil.rmtree(project)
                            if os.path.exists('projects') and os.path.isdir('projects'):
                                shutil.rmtree('projects')
                            st.cache_data.clear()
                            st.rerun()
                            
                        else:
                            # Handle other OS errors and show me
                            st.write(f"An unexpected OSError occurred: {e}") 
            else:
                st.stop()
            
            # prepare data
            df = pd.read_csv(f'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/{project}/processed_data_ready.csv', dtype = {'rfid':str})
            
            # edge
            # finding where the extracted files are
            base = os.getcwd()
            log_action(logger, f'base path: {base}')
            target1 = os.path.join(base, 'tscc', 'projects', 'ps-palmer', 'gwas', 'projects', project)
            target2 = os.path.join(base, 'projects', 'ps-palmer', 'gwas', 'projects', project)
            target3 = os.path.join(base, project)
            log_action(logger, f'tscc: {os.path.isdir(target1)}')
            log_action(logger, f'project: {os.path.isdir(target2)}')
            log_action(logger, f'root: {os.path.isdir(target3)}')

            if os.path.isdir(target1):
                path = target1 + '/'
            elif os.path.isdir(target2):
                path = target2 + '/'
            else:
                path = target3 + '/'
            
            log_action(logger, f'final path: {path}')

            if not os.path.isdir(path):
                # 
                st.write('The files are currently not available, please select a different version and try again.')
                st.stop()
            
            # getting genotype path
            geno_path =  os.path.join(base,'genotypes') + '/genotypes'
            founder_path =  os.path.join(base,'founder_genotypes') + '/founder7.2'
                
            if len(path) > 0:
                # init
                log_action(logger, f'{filename}: initializing')
                gwas = gwas_pipe(path = path,
                             data = df,
                             project_name = f'{project}',
                             n_autosome =20,
                             all_genotypes =  geno_path,
                             traits = [], 
                             threshold=5.36,
                             founderfile = founder_path,
                             locuszoom_path='GWAS_pipeline/locuszoom/',
                             phewas_db = 'https://palmerlab.s3.sdsc.edu/tsanches_dash_genotypes/gwas_results/phewasdb_rn7_g102.parquet.gz',
                             threads = 6,
                             gtf = f'https://www.dropbox.com/scl/fi/ai1fw6fxsazns0pt40yec/rn_7_gtf.csv?rlkey=ovyi0mdaz71oci9mhtxchhvxw&dl=1')
                self = gwas
                st.session_state['gwas'] = self

        if 'gwas' in st.session_state:
            # if changed option but don't want to init object again
            self = st.session_state['gwas']
            st.write('##### Phenotype Wide Association Study (PheWAS): ')
            phewas(self)
            st.write('##### Locuszoom Plot: ')
            locuszoom(self)

            if st.button("Refresh"):
                # hard clear
                reset()
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
    
    st.image('./assets/Manhattan-Black-Roboto-font-4-alt-5.png')
    st.image('https://palmerlab.org/wp-content/uploads/2019/09/palmerlab-logo.png')