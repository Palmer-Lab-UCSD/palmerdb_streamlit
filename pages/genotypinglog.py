"""
Genotyping Page
"""

import streamlit as st
import numpy as np
import pandas as pd
from components.logger import *
from components.authenticate import *
import os
import time
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

@st.cache_data
def convert_df(df):

    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

authenticator, username, hidden, admin, is_logged_in= start_auth()
if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
else:
    st.write('Please sign in.')

if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

if is_logged_in and admin in username: 

    st.title('Genotyping Logs')

    conn = st.connection("palmerdb", type="sql", autocommit=False)

    tab1, tab2 = st.tabs(['Genotyping Log','Genotyping Drops'])

    with tab1:
        genotyping_log_query = 'select * from genotyping.genotyping_log_view'

        # lists of values for filters
        rounds = conn.query('select distinct round_calculated from genotyping.genotyping_log_view').round_calculated.unique().tolist()
        projects =  conn.query('select distinct project_name from genotyping.genotyping_log_view').project_name.unique().tolist()
        libraries =  conn.query('select distinct library_name from genotyping.genotyping_log_view').library_name.unique().tolist()

        st.subheader('Genotyping Log')
        st.write('Hover over the table to find a search button in the upper right to search RFIDs.')

        col1, col2, col3, col4 = st.columns(4)
        # dropdown filters
        with col1:
            ground = st.selectbox(options=sorted(rounds,reverse=True),
                                label='Choose genotyping round:',
                                index=0,
                                help='Required, default: latest')
        with col2:
            glibrary = st.multiselect(options=sorted(libraries, reverse=True), label='Enter library to search:',
                                    placeholder='Click or type library name')
        with col3:
            gproject = st.multiselect(options=sorted(projects), label='Enter project to search:',
                                    placeholder='Click or type project name')
        with col4:
            gstage = st.selectbox(options=['snp_and_sample_filtered', 'raw','snp_filtered'], 
                                label='Choose filtering stage',
                                index=0,
                                help='Required, default: snp_and_sample_filtered',
                                key=0)

        genotyping_log_query += f" where round_calculated = '{ground}' " # leave space

        # run filters
        if glibrary:
            glibrarysep = ", ".join(f"'{x}'" for x in glibrary)
            genotyping_log_query += f'and library_name in ({glibrarysep}) ' # leave space
        if gproject:
            gprojectsep = ", ".join(f"'{x}'" for x in gproject)
            genotyping_log_query += f'and project_name in ({gprojectsep}) ' # leave space
        if gstage:
            genotyping_log_query += f"and filtering_stage = '{gstage}' " # leave space

        # run query
        gl = conn.query(genotyping_log_query)
        st.dataframe(gl,hide_index=True)
        st.write(gl.shape[0], ' rows')

        csv = convert_df(gl)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f'n{len(gl)}_genotyping_log_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

    with tab2:
        st.subheader('Genotyping Drops')
        st.write('Hover over the table to find a search button in the upper right to search RFIDs.')
        col5, col6 = st.columns(2)

        # lists of possible values for filters
        drop_round = conn.query('select distinct round_calculated from genotyping.drops_log_view').round_calculated.unique().tolist()
        drop_lib = conn.query('select distinct library_name from genotyping.drops_log_view where lib_round_dropped is not NULL').library_name.unique().tolist()
        drop_proj = conn.query('select distinct project_name from genotyping.drops_log_view where proj_round_dropped is not NULL').project_name.unique().tolist()
        
        # filter dropdowns
        with col5:
            dround = st.multiselect(options=sorted(drop_round,reverse=True),
                                    default=drop_round,
                                    label='Choose genotyping round:',
                                    help='Required, default: latest')
        with col6:
            dstage = st.multiselect(options=['Library','Project','Metadata', 'Demux','Bam','Sex','Heterozygosity','Missingness','Mendelian Error'], 
                                    label='Stages of QC to Display',
                                    placeholder='Choose which stages of QC to display info in table')

        # map column selection
        if dstage:
            stage_dict = {'Library' :['lib_round_dropped','lib_redo_status','lib_notes'],
                        'Project':['proj_round_dropped','project_notes'],
                        'Metadata':['rfid_not_missing_data_list','hsrats_only','rfid_non_multizero',
                                    'rfid_not_short', 'sampleid_not_dup','unresolvable_sid',
                                    'metadata_qc_status','metadata_notes'],
                        'Demux':['fastq_exists','small_fastq_size', 'demux_qc_status','demux_notes'],
                        'Bam':['markdup_bam_file_exists','enough_non_duplicate_reads','bam_qc_status','bam_notes'],
                        'Sex':['sex_qc_outcome','sex_qc_status','sex_notes'],
                        'Heterozygosity':['heterozygosity_qc_outcome','heterozygosity_qc_status','heterozygosity_notes'],
                        'Missingness':['missingness_qc_status','missingness_notes'],
                        'Mendelian Error':['mendelian_error_status','mendelian_notes']
                        }
            stage_list = []
            for x in dstage:
                stage_list.extend(stage_dict[x])
            dstagesep = ", ".join(f"{x}" for x in stage_list)
            drop_query = f'select rfid, library_name, barcode, round_calculated, {dstagesep} from genotyping.drops_log_view '

        else:
            drop_query = 'select * from genotyping.drops_log_view ' # leave space

        # filter to rounds 
        droundsep = ", ".join(f"'{x}'" for x in dround)
        drop_query += f" where round_calculated in ({droundsep}) " # leave space

        # run query
        dl = conn.query(drop_query)
        st.dataframe(dl,hide_index=True)
        st.write(dl.shape[0], ' rows')

        csv = convert_df(dl)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f'n{len(dl)}_genotyping_drops_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )

        # counts of dropped samples in each stage
        st.write('Drop Counts')
        count_query = f'''select rfid, library_name, barcode, round_calculated, 
        lib_round_dropped, proj_round_dropped, metadata_qc_status, demux_qc_status,
        bam_qc_status, sex_qc_status, heterozygosity_qc_status, missingness_qc_status, 
        mendelian_error_status from genotyping.drops_log_view
        where round_calculated in ({droundsep})'''
        dl_count = conn.query(count_query)
        counts = pd.DataFrame(dl_count[['lib_round_dropped', 'proj_round_dropped',
                                'metadata_qc_status','demux_qc_status', 'bam_qc_status',
                                'sex_qc_status','heterozygosity_qc_status',
                                'missingness_qc_status', 'mendelian_error_status']].count().reset_index().rename(columns={'index': 'drop_stage', 0: 'count'}))
        st.dataframe(counts,hide_index=True)


with st.sidebar:
    st.markdown('''
    [ratgenes.org](https://ratgenes.org)
    
    [Palmer Lab website](https://palmerlab.org)
    
    [ratgtex.org](https://ratgtex.org)
    
    Palmer Lab IRS
    ''')
    with st.container(border=True):
        st.write('##### :green[Support]')
        st.markdown("For website support, please contact the Palmer Lab.")
    
    st.image('./assets/Manhattan-Black-Roboto-font-4-alt-5.png')
    st.image('https://palmerlab.org/wp-content/uploads/2019/09/palmerlab-logo.png')