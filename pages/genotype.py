"""
# Genotype Reports/UCSD Library
"""
import streamlit as st
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
    hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary"])
elif is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
    def logout():
        authenticator.logout()
    with st.sidebar:
        st.write(f"Welcome, {authenticator.get_username()}!")
        st.button("Logout", "logout_btn", on_click=logout)
    if username != 'admin':
        hide_pages(["Database Summary", "Sample Tracking", "Data Dictionary"])
# content
st.title('Genotype Reports')

st.markdown(
    """
    The genotyping reports are available at the UC San Diego Library Digital Collections.
    
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
    - **LATEST: ["round10.2", mRatBN7.2, 2024-01-18](https://library.ucsd.edu/dc/object/bb29129987)**
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
    ''')