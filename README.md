# palmerdb_streamlit
This repo is for the code used to create and maintain the streamlit application for viewing database summaries.

Setup:

##### home.py 
This is the main page and the python file used to start the application.
##### .streamlit
This directory contains ```config.toml```, ```pages.toml```, and a secrets file for the database connection.
```config.toml``` sets the theme of the app.
```pages.toml``` sets the layout of the sidebar to display pages.

##### pages
This directory contains pages which appear in the app apart from the main page. Each python file is an individual page. Current pages are split into Palmer Lab access and public access sections.


To run:
```
streamlit run home.py
```
