![alt text](https://github.com/Palmer-Lab-UCSD/palmerdb_streamlit/blob/main/assets/irs.png?raw=true)
# 
This repository is for the code used to create and maintain the Internet Rat Server (IRS) Streamlit application, intended as a user-friendly view for information from the Palmer Lab's database.

### To launch:
The main method of running this app is through an AWS ECS Service  ```streamlit``` as a Fargate instance, created from a Docker image stored in AWS ECR. To run the app locally, use the command:
```
streamlit run home.py
```
---
### Repository Structure
```home.py```: This is the main page and the python file used to start the application.
#### Directories
##### .streamlit
This directory contains ```config.toml``` and ```pages.toml```; additional files ```auth.env``` and ```secrets.toml``` are set locally for authentication and database connection respectively.

```config.toml``` sets the theme of the app.

```pages.toml``` sets the layout of the sidebar to display pages.

##### pages
This directory contains pages which appear in the app apart from the main page. Each python file is an individual page. Current pages are split into Palmer Lab access and public access sections. The pages are built with [streamlit-pages](https://github.com/blackary/st_pages).

##### components
Contains authentication and logging components, functions for MedPC extractor.

##### GWAS_pipeline
This is cloned from the Palmer Lab GWAS pipeline repository. Contains relevant files for GWAS tools. The GWAS class in the pipeline repository is overwritten and replaced with ```gwas_class_auto.py``` from this repo.

#### Other Files
##### In repository:

```gwas.yml```: General Conda environment 

```lzenv.yml```: Conda environment specifically for locuszoom functionality

```template.py```: Empty page template, including standard imports and authentication setup.

##### Local Files:

```founder_genotypes```: Directory of PLINK binary files (bed/bim/fam) for founders. *Must be saved locally*

```genotypes```: Directory of PLINK binary files (bed/bim/fam) for HS rats, latest version. *Must be saved locally. [Available with all public genotype releases.](https://irs.ratgenes.org/Genotyping%20Reports)*


### Tools
Authentication is done through [AWS Cognito](https://aws.amazon.com/cognito/). The application is deployed with [AWS Elastic Container Service](https://aws.amazon.com/ecs/).

This application was developed as a project for the [Palmer Lab](https://palmerlab.org) with [Streamlit](https://streamlit.io).

### Related Resources
[ratgenes.org](https://ratgenes.org/)

[RatGTEx](https://ratgtex.org/)

The IRS logo is a derivative work from the logo for the Center for Genetics, Genomics, and Epigenetics of Substance Use Disorders in Outbred Rats. 
