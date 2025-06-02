"""
# This page is an overview for the numbers in the database.
"""

import streamlit as st
import numpy as np
import pandas as pd
import time
from components.logger import *
from components.authenticate import *
import os
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors
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
else:
    st.write('Please sign in.')

if is_logged_in and admin not in username:
    st.write('You do not have permission, sorry! Please contact the Palmer Lab if you think this is a mistake.')

if is_logged_in and admin in username:
        st.title('Palmer Lab Database Summary')

        # for download button
        @st.cache_data
        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv().encode('utf-8')
        
        
        # db connection
        # creds in secret
        conn = st.connection("palmerdb", type="sql", autocommit=False)
        log_action(logger, f'{filename}: db connection made')

        # project list
        project = conn.query("select distinct project_name from sample_tracking.project_metadata order by project_name")
        project = project.project_name.tolist()
        log_action(logger, f'{filename}: project list acquired')

        options = st.multiselect(label='Select project', 
                       options=project, default=None, 
                       placeholder="Choose an option", disabled=False, label_visibility="visible")
        # options = ','.join([f"'{option}'" for option in options])

        # query text
        sql = '''
            rollback;
            begin transaction;
               with tissue as 
                        (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS tissue
                        FROM sample_tracking.sample_metadata sm
                        JOIN sample_tracking.tissue gl ON sm.rfid = gl.rfid
                        GROUP BY sm.project_name),
               dna as 
                       (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS dna_extracted
                        FROM sample_tracking.sample_metadata sm
                        JOIN sample_tracking.extraction_log gl ON sm.rfid = gl.rfid
                        GROUP BY sm.project_name),
               sequenced as 
                       (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS sequenced
                        FROM sample_tracking.sample_metadata sm
                        LEFT JOIN sample_tracking.sample_barcode_lib gl ON sm.rfid = gl.rfid
                        GROUP BY sm.project_name),
               genotype as 
                       (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS genotyped
                        FROM  sample_tracking.sample_metadata sm
                        JOIN sample_tracking.genotyping_log_total gl ON sm.rfid = gl.rfid
                        GROUP BY sm.project_name),
               redo AS 
                    (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS redo
                    FROM sample_tracking.sample_metadata sm
                    JOIN sample_tracking.genotyping_log_total gl ON sm.rfid = gl.rfid
                    WHERE gl.sample_use LIKE 're%'
                    GROUP BY sm.project_name),
               ship as (select project_name, count(project_name) as shipped from sample_tracking.sample_metadata group by project_name),
               rna as 
                        (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS rna_sent
                        FROM sample_tracking.sample_metadata sm
                        JOIN sample_tracking.rna gl ON sm.rfid = gl.rfid
                        GROUP BY sm.project_name),
               rna_extract as 
                       (SELECT sm.project_name, COUNT(DISTINCT gl.rfid) AS rna_extracted
                        FROM sample_tracking.sample_metadata sm
                        JOIN sample_tracking.rna_extraction_log gl ON sm.rfid = gl.rfid
                        GROUP BY sm.project_name)

                SELECT 
                    distinct pm.project_name, 
                    coalesce(h.shipped, 0) as shipped,
                    COALESCE(t.tissue, 0) AS tissue, 
                    COALESCE(d.dna_extracted, 0) AS dna_extracted, 
                    COALESCE(s.sequenced, 0) AS sequenced, 
                    COALESCE(g.genotyped, 0) AS genotyped,
                    COALESCE(r.redo, 0) AS redo,
                    COALESCE(rna.rna_sent, 0) AS rna_received,
                    COALESCE(rne.rna_extracted, 0) AS rna_extracted
                FROM 
                    sample_tracking.project_metadata pm
                LEFT JOIN tissue t ON pm.project_name = t.project_name
                LEFT JOIN dna d ON pm.project_name = d.project_name
                LEFT JOIN sequenced s ON pm.project_name = s.project_name
                LEFT JOIN genotype g ON pm.project_name = g.project_name
                LEFT JOIN redo r ON pm.project_name = r.project_name
                left join ship h on pm.project_name = h.project_name
                left join rna rna on pm.project_name = rna.project_name
                left join rna_extract rne on pm.project_name = rne.project_name

                order by pm.project_name
        '''
        
        # make connection
        if 'full' not in st.session_state:
            pheno_tables = conn.query('''SELECT table_schema, table_name
                            FROM information_schema.tables
                            WHERE table_name = 'gwas_phenotypes'
                            AND table_type = 'BASE TABLE'
                            AND table_schema NOT IN ('pg_catalog', 'information_schema')
                            ''')
            pheno_proj = pheno_tables.table_schema.unique().tolist()
            pheno = pd.DataFrame()        
            for proj in pheno_proj:
                proj_pheno = conn.query(f'''select coalesce(count(*),0) as phenotyped, 
                                            '{proj}' as project_name from {proj}.gwas_phenotypes''')
                pheno = pd.concat([pheno, proj_pheno])

            df = conn.query(sql)
            log_action(logger, f'{filename}: form dataframe')
            df = df.merge(pheno,how='left',on='project_name')
            df.phenotyped.fillna(0,inplace=True)
            st.session_state['full'] = df
            
        df = st.session_state['full']

        # filter selected projects
        if len(options) > 0:
            log_action(logger, f'{filename}: filter dataframe')
            df = df.loc[df.project_name.isin(options)]

        # display df, shape
        df = df[['project_name', 'shipped', 'phenotyped', 'tissue', 'dna_extracted', 'sequenced', 
                 'genotyped', 'redo', 'rna_received', 'rna_extracted']]
        st.dataframe(df, hide_index=True)

        st.write(len(df), ' projects')

       
        # download
        csv = convert_df(df) 
        st.download_button(
            label="Download summary as CSV",
            data=csv,
            file_name=f'n{len(df)}_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
        
        if len(options) == 1:
            
            # fig = px.funnel_area(names=['shipped', 'phenotyped', 'tissue', 
            #                             'dna_extracted', 'sequenced', 'genotyped'],
            #         values=df.iloc[0,1:7])
            # st.plotly_chart(fig)

#         compare = st.selectbox(label='Select comparison column', 
#                        options=['phenotyped', 'tissue', 
#                                 'dna_extracted', 'sequenced','genotyped'], index=None, 
#                        placeholder="Choose an option", disabled=False, label_visibility="visible",
#                        help='Shows the difference compared to selected column')
        
#         def create_diff_df(df, selected_column):
#             """
#             Parameters:
#             df: Original DataFrame with project metrics
#             selected_column: Column to subtract from others (one of: 'shipped', 'phenotyped', 
#                             'tissue', 'dna_extracted', 'sequenced')

#             Returns:
#             DataFrame with project_name and difference columns
#             """
#             # Columns to subtract from (exclude non-metric columns and selected column)
            

#             # Create new DF with project names
#             df_diff = df[['project_name', 'shipped', selected_column]].copy()

#             # Calculate differences for each target column
#             for col in ['phenotyped', 'tissue', 'dna_extracted', 
#                        'sequenced', 'genotyped']:
#                 if col != selected_column:  # Avoid subtracting from itself
#                     new_col = f"{col} - {selected_column}"
#                     df_diff[new_col] = df[col] - df[selected_column]
#                     df_diff.loc[df_diff[new_col] < 0, new_col] = None

#             return df_diff
            
#         if compare:
#             diff= create_diff_df(df, compare)
#             st.dataframe(diff, hide_index=True)

            # Create a funnel chart with two traces
            track_cols = ['shipped', 'phenotyped', 'tissue', 'dna_extracted', 'sequenced', 'genotyped']
            counts = df.iloc[0,1:7].tolist()
            fig = go.Figure(go.Funnel(
                name='Initial Name 1',
                y=track_cols,
                x=counts))
            
            fig.update_traces(
                marker=dict(
                    color=plotly.colors.sequential.Plasma[2:8],   # Name of the colorscale
                    showscale=True          # Show the colorbar
                ),
                selector=dict(type='funnel')
            )


            # Update the name of all funnel traces
            fig.update_traces(name='Updated Funnel', selector=dict(type='funnel'))

            st.plotly_chart(fig)
            
        # force refresh
        if st.button('Refresh', on_click = st.cache_data.clear()):
            log_action(logger, f'{filename}: refresh button clicked')
            st.cache_data.clear()

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