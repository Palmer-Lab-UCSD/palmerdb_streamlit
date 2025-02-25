"""
# All Trait Correlations
"""

import streamlit as st
import numpy as np
import pandas as pd
import time
import io
import matplotlib.pyplot as plt
from components.logger import *
from components.authenticate import *
import os
from streamlit_cognito_auth import CognitoAuthenticator
from dotenv import load_dotenv
from st_pages import show_pages_from_config, add_indentation, hide_pages
pd.set_option("styler.render.max_elements", 2000000)
pd.options.display.float_format = '{:.4f}'.format
st.set_page_config(
    page_title="Palmer Lab Database",
    page_icon="🐀",
    layout="wide",
    initial_sidebar_state="auto"
)

# for download button
@st.cache_data
def convert_df(df):
    '''IMPORTANT: Cache the conversion to prevent computation on every rerun'''
    return df.to_csv().encode('utf-8')
        
def colorbar(vmin: float, vmax: float, cmap: str):
    '''display a color bar'''
    fig, ax = plt.subplots(figsize=(6, 0.25))
    fig.subplots_adjust(bottom=0.5)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), 
                      cax=ax, orientation='horizontal')
    ticks = [vmin, (vmin + vmax) / 2, vmax]
    cb.set_ticks(ticks)
    cb.set_ticklabels([f"{ticks[0]:.2f}", f"{ticks[1]:.2f}", f"{ticks[2]:.2f}"])
    cb.ax.tick_params(labelsize=6)
    st.pyplot(fig)
    
st.title('Trait Correlations')
st.write('''
         This tool displays the rG, rGse, and p-value between two traits. To begin, select a project from either dropdown. 
         
         Select a second project from the other dropdown to compare, or leave it blank to view traits from all projects.
         - The page sidebar on the left can be closed with the X if the table is truncated.
         - The columns can be sorted by clicking on the column titles. 
         - Use the toggles to highlight certain columns based on the gradient scales shown.
         - Use the download button below the table to download the selection.
         
         ''')

logger = setup_logger()
filename = os.path.basename(__file__)

log_action(logger, f'{filename}: app started')

authenticator, username, hidden, admin, is_logged_in= start_auth()

if is_logged_in:
    log_action(logger, f'{filename}: authentication status: true, user name: {username}')
    # read file and organize df
    df = pd.read_parquet("allgenetic_correlations.parquet.gz")
    df['project1'] = df.trait1.str.split(':').str[0]
    df['trait1'] = df.trait1.str.split(':').str[1]
    df['project2'] = df.trait2.str.split(':').str[0]
    df['trait2'] = df.trait2.str.split(':').str[1]
    df = df[['project1', 'trait1', 'rG', 'rGse', 'rG_string', 'pval', 'trait2', 'project2']]

    projects1 = sorted(set(df.project1.tolist()))
    projects2 = sorted(set(df.project2.tolist()))

    # split selection
    col1, col2 = st.columns(2)
    with col1:
        proj1 = st.selectbox(label="Select project of trait 1:", options=projects1, index=None, 
                             placeholder="Choose a project",
                             help='Controls the project on the left of the table. Click the X to clear the selection.')


    with col2: 
        proj2 = st.selectbox(label="Select project of trait 2:", options=projects2, index=None, 
                             placeholder="Choose a project",
                             help='Controls the project on the right of the table. Click the X to clear the selection.')

    # filter
    if proj1:
        df = df.loc[df.project1.str.contains(proj1)]
        log_action(logger, f'{proj1}: as project 1')

    if proj2:
        df = df.loc[df.project2.str.contains(proj2)]
        log_action(logger, f'{proj2}: as project 2')

    if proj1 or proj2:
        # don't do anything until a project is selected
        with col1:
            # select rg
            rg_threshold = st.select_slider("rG threshold", 
                     options=[round(x, 2) for x in (i * 0.01 for i in range(0, 101))], 
                     value=0,
                     help="Show only entries with absolute value rG value above this threshold", 
                     label_visibility="visible")
            colorbar(-1, 1, 'coolwarm')
            highlight_rg = st.toggle("Color rG")

        with col2:
            # select pval
            p_threshold = st.select_slider("p-value threshold", 
                     options=[round(x, 2) for x in (i * 0.01 for i in range(0, 51))], 
                     value=0,
                     help="Show only entries with p-value above this threshold", 
                     label_visibility="visible")
            colorbar(0, 0.5, 'Oranges')
            highlight_p = st.toggle("Color p-value")

        # filter
        df = df.loc[df.rG.abs() > rg_threshold]
        df = df.loc[df.pval > p_threshold]

        # color toggles
        if highlight_rg and highlight_p:
            display = df.style.background_gradient(subset=['rG'], cmap='coolwarm', vmin=-1, vmax=1)\
                        .background_gradient(subset=['pval'], cmap='Oranges', vmin=0)
        elif highlight_rg:
            display = df.style.background_gradient(subset=['rG'], cmap='coolwarm', vmin=-1, vmax=1)
        elif highlight_p:
            display = df.style.background_gradient(subset=['pval'], cmap='Oranges', vmin=0)
        else:
            display = df.style.format({"rG": "{:.6f}", "rGse": "{:.6f}", "pval": "{:.6f}"})

        # display df (copy)
        st.dataframe(display, width = 2000, hide_index=True,
                     column_config={"project1":st.column_config.Column(
                                            "project1", 
                                            width='small'),
                                   "project2":st.column_config.Column(
                                            "project2", 
                                            width='small')})
        st.write(df.shape[0], ' rows')
        
        log_action(logger, f'current rg threshold: {rg_threshold}')
        log_action(logger, f'current pval threshold: {p_threshold}')
        log_action(logger, f'rg highlight status: {highlight_rg}')
        log_action(logger, f'pval highlight status: {highlight_p}')

        # download
        csv = convert_df(df) 
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f'trait_correlations_n{len(df)}_{time.strftime("%Y%m%d")}.csv',
            mime='text/csv',
        ) 
        
else:
    st.write('Please sign in.')


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