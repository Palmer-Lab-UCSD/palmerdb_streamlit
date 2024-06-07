# palmerdb_streamlit
This repo is for the code used to create and maintain the Internet Rat Server (IRS) Streamlit application for viewing database summaries.

##### home.py 
This is the main page and the python file used to start the application.
##### .streamlit
This directory contains ```config.toml```, ```pages.toml```, ```auth.env```, and a secrets file for the database connection.
```config.toml``` sets the theme of the app.

```pages.toml``` sets the layout of the sidebar to display pages.

```auth.env``` contains AWS Cognito authentication details.

```secrets.toml``` should be set locally to include the database connection options.

##### pages
This directory contains pages which appear in the app apart from the main page. Each python file is an individual page. Current pages are split into Palmer Lab access and public access sections. The pages are built with [streamlit-pages](https://github.com/blackary/st_pages).

##### components
Contains authentication and logging components, functions for MedPC extractor.

##### GWAS_pipeline
Contains relevant files for GWAS tools.

### To launch:
The main method of running this app is through an AWS ECS Service  ```streamlit``` as a Fargate instance. Within the instance, the application is run through a Docker container. To run the files locally, use the command:
```
streamlit run home.py
```

### Tools
Authentication is done through [AWS Cognito](https://aws.amazon.com/cognito/). The application is deployed with [AWS Elastic Container Service](https://aws.amazon.com/ecs/).

This application was developed as a project for the [Palmer Lab](https://palmerlab.org) with [Streamlit](https://streamlit.io).
