# palmerdb_streamlit
This repo is for the code used to create and maintain the streamlit application for viewing database summaries.

##### home.py 
This is the main page and the python file used to start the application.
##### .streamlit
This directory contains ```config.toml```, ```pages.toml```, and a secrets file for the database connection.
```config.toml``` sets the theme of the app.
```pages.toml``` sets the layout of the sidebar to display pages.
```secrets.toml``` should be set locally to include the database connection options.

##### pages
This directory contains pages which appear in the app apart from the main page. Each python file is an individual page. Current pages are split into Palmer Lab access and public access sections. The pages are built with [streamlit-pages](https://github.com/blackary/st_pages).

##### components
Switched authorization method -- currently unused.

### To launch:
The main method of running this app is through an AWS EC2 instance ```streamlit_db```. Within the instance, the application is run through:
```
streamlit run home.py
```

This app was created with [streamlit](https://streamlit.io/). 
