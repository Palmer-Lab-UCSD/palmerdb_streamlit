# palmerdb_streamlit
This repo is for the code used to create and maintain the Internet Rat Server (IRS) Streamlit application for viewing database summaries.

##### home.py 
This is the main page and the python file used to start the application.
##### .streamlit
This directory contains ```config.toml```, ```pages.toml```, ```auth.env```, and a secrets file for the database connection.
```config.toml``` sets the theme of the app.

```pages.toml``` sets the layout of the sidebar to display pages.

```auth.env``` contains AWS Cognito authentication details and relevant environment variables. This is set locally.

```secrets.toml``` should be set locally to include the database connection options.

##### pages
This directory contains pages which appear in the app apart from the main page. Each python file is an individual page. Current pages are split into Palmer Lab access and public access sections. The pages are built with [streamlit-pages](https://github.com/blackary/st_pages).

##### components
Contains authentication and logging components, functions for MedPC extractor.

##### GWAS_pipeline
This is cloned from the Palmer Lab GWAS pipeline repo. Contains relevant files for GWAS tools. The GWAS class in the pipeline repo is overwritten and replaced with ```gwas_class_auto.py``` from this repo.

#### Other Files
**In repository:**
```gwas.yml```: General Conda environment 

```lzenv.yml```: Conda environment specifically for locuszoom functionality

```template.py```: Empty page template including standard imports and authentication setup.

**Local Files:**
```founder_genotypes```: Directory of PLINK binary files (bed/bim/fam) for founders. *Must be saved locally*

```genotypes```: Directory of PLINK binary files (bed/bim/fam) for HS rats, latest version. *Must be saved locally. [Available with all public genotype releases.](https://irs.ratgenes.org/Genotyping%20Reports)*


### To launch:
The main method of running this app is through an AWS ECS Service  ```streamlit``` as a Fargate instance. The instance is created from a Docker image. To run the files locally, use the command:
```
streamlit run home.py
```

### Tools
Authentication is done through [AWS Cognito](https://aws.amazon.com/cognito/). The application is deployed with [AWS Elastic Container Service](https://aws.amazon.com/ecs/).

This application was developed as a project for the [Palmer Lab](https://palmerlab.org) with [Streamlit](https://streamlit.io).
