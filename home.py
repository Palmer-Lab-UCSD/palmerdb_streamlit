"""
# Palmer Lab Database Dashboard Home
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
st.set_page_config(
    page_title="Palmer Lab Database",
    page_icon="🐀",
    layout="wide",
    initial_sidebar_state="auto"
)
logger = setup_logger()
filename = os.path.basename(__file__)

log_action(logger, f'{filename}: app started')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')


# padding line
st.write('######') 
# title
st.image('./assets/irs.png')
st.header("", divider='green')
# st.header("Palmer Lab Database 🐀", divider='green')

# body
st.write(
    """
    The Internet Rat Server (IRS) serves as a dashboard for the Palmer Lab database.
    
    To access tools, please sign in with the given account using the form in the left sidebar.  
    View a list of available tools below.
    
    This app was developed as a project for the [Palmer Lab](https://palmerlab.org), and was created with [streamlit](https://streamlit.io).
"""
)

with st.container(border=True):
    st.write('##### :green-background[Navigation]')
    navi = st.chat_message('Palmer Lab', avatar='./assets/chat.png')
    navi.write("Login to see a list of tools available to you!")
    if is_logged_in:
        if admin in username: 
            navi.write('''**:green[Palmer Lab Tools:]**  
                            Database Summary: View animal counts throughout the progress of a project.  
                            Sample Tracking: Check the progress of animals and projects through the genotyping process.  
                            Data Dictionary: View the data dictionary of a project used for GWAS.  
                            Genotyping Metadata: Retrieve the metadata table for a pool of flowcells.  
                            Database Records: View Palmer Lab database phenotype and metadata tables per project.  
                            HS West Records: HS West Colony birth, prediction, and genotyping records.  
                         ''')
        navi.write("""**:blue[User Tools:]**  
                        MedPC Extractor: Upload MedPC files and display the values as a table.  
                        Regional Association Tools: Build PheWAS tables and locuszoom plots with data from a report.  
                        GWAS Reports: View an archive of GWAS reports for a project.  
                        Rat Metadata: View Palmer Lab records for any rat given its RFID.  
                        Database Records: View Palmer Lab database phenotype and metadata tables per project.  
                        Trait Correlations: Compare traits between two projects.  
                         """)
    navi.write("""**:violet[Public Resources:]**  
                        Genotyping Reports: View data and records from our genotyping reports.
                    """)
    

with st.sidebar:
    st.markdown('''
    [ratgenes.org](https://ratgenes.org)
    
    [Palmer Lab website](https://palmerlab.org)
    
    [ratgtex.org](https://ratgtex.org)
    
    Palmer Lab IRS
    ''')
    with st.container(border=True):
        st.write('##### :green[Support]')
        st.write("For website support, please contact the Palmer Lab, or Elaine directly at ekeung@health.ucsd.edu.")
    
    st.image('./assets/Manhattan-Black-Roboto-font-4-alt-5.png')
    st.image('https://palmerlab.org/wp-content/uploads/2019/09/palmerlab-logo.png')
    

    
    

