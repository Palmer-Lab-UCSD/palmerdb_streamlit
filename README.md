![alt text](https://github.com/Palmer-Lab-UCSD/palmerdb_streamlit/blob/main/assets/irs.png?raw=true)
# 
This repository is for the code used to create and maintain the Internet Rat Server (IRS) Streamlit application, intended as a user-friendly view for information from the Palmer Lab's database.

### To launch:
The main method of running this app is through an AWS ECS Service  ```streamlit``` as a Fargate instance, created from a Docker image stored in AWS ECR. To run the app locally, use the command:
```
streamlit run home.py
```
---

### Tools
Authentication is done through [AWS Cognito](https://aws.amazon.com/cognito/). The application is deployed with [AWS Elastic Container Service](https://aws.amazon.com/ecs/).

This application was developed as a project for the [Palmer Lab](https://palmerlab.org) with [Streamlit](https://streamlit.io).

### Local Files
A database connection, the latest set of HS rats genotypes, and founder genotypes are required to enable full functionality.

### Related Resources
[ratgenes.org](https://ratgenes.org/)

[RatGTEx](https://ratgtex.org/)

The IRS logo is a derivative work from the logo for the Center for Genetics, Genomics, and Epigenetics of Substance Use Disorders in Outbred Rats. 
