"""
# Genotype Reports/UCSD Library
"""
import streamlit as st
import hmac
import components.authenticate as authenticate
from st_pages import show_pages_from_config, add_indentation, hide_pages
st.set_page_config(
    page_title="Palmer Lab Database Samples",
    page_icon="🐀",
    layout="wide",
    initial_sidebar_state="auto"
)

# Check authentication 
authenticate.set_st_state_vars()
# Add login/logout buttons
if st.session_state["authenticated"]:
    authenticate.button_logout()
else:
    authenticate.button_login()

# show pages, hide palmer pages
add_indentation()
show_pages_from_config()
if "palmerlab" not in st.session_state["user_cognito_groups"]:
    hide_pages(["Database Summary", "Sample Tracking"])

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
