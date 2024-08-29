"""
# Genotype Reports/UCSD Library
"""
import streamlit as st
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

log_action(logger, f'{filename}: page entered')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')


if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

# content
st.title('Genotype Reports')

st.markdown(
    """
    Genotyping reports are available at the UC San Diego Library Digital Collections.
    
    [Genotype data from: NIDA Center for GWAS in Outbred rats](https://library.ucsd.edu/dc/collection/bb5403210b)
    
    The contents of the deposits includes the following:
    - PLINK binary format
        - .bed
        - .bim
        - .fam
    - Variant Call Format
        - .vcf.gz
        - .vcf.gz.tbi
    - Genotype Log and Quality Report
        - genotyping_log.csv
        - report.html
    
    They can be found at the following links:
    - **["round10.4", mRatBN7.2, 2024-07-01](https://library.ucsd.edu/dc/object/bb65996027) [LATEST]**
    - ["round10.3", mRatBN7.2, 2024-05-29](https://library.ucsd.edu/dc/object/bb08998715)
    - ["round10.2", mRatBN7.2, 2024-01-18](https://library.ucsd.edu/dc/object/bb29129987)
    - ["round10.1", mRatBN7.2, 2023-07-12](https://library.ucsd.edu/dc/object/bd6647448j)
    - ["round10", mRatBN7.2, 2023-02-22](https://library.ucsd.edu/dc/object/bb0079998p)
    - ["round8", rn6, 2019-08-15](https://library.ucsd.edu/dc/object/bb15123938)

    A repository for low-coverage sequenced HS rats (trimmed fastqs) which have been successfully genotyped in the genotyping round "round10.1" is stored on the Sequence Read Archive:
    - [BioProject Accession Number: PRJNA1022514](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1022514)
    """
)

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