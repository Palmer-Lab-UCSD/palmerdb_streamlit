# Use Miniconda as a base image
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y default-jre

# Clone the repository
RUN git clone https://github.com/Palmer-Lab-UCSD/palmerdb_streamlit.git


# Copy all files from the current directory to the working directory
COPY auth.env /app/palmerdb_streamlit/.streamlit/
COPY secrets.toml /app/palmerdb_streamlit/.streamlit/
COPY founder_genotypes /app/palmerdb_streamlit/
COPY genotypes /app/palmerdb_streamlit/
COPY GWAS_pipeline /app/palmerdb_streamlit/
RUN mv /app/palmerdb_streamlit/gwas_class_auto.py /app/palmerdb_streamlit/GWAS_pipeline
# Set working directory to the cloned repository
WORKDIR /app/palmerdb_streamlit

# Update conda and add the conda-forge channel
RUN conda update -n base -c defaults conda
RUN conda config --add channels conda-forge
RUN conda config --add channels bioconda
RUN conda config --add channels defaults

# Create the conda environment from the gwas.yml file
RUN conda env create -f gwas.yml
RUN conda env create -f lzenv.yml

# Ensure the conda environment is activated for all subsequent RUN commands
SHELL ["conda", "run", "-n", "gwas", "/bin/bash", "-c"]

# Upgrade pip and install any additional packages if necessary
# Uncomment if there are additional requirements in requirements.txt
# RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && rm -rf requirements.txt

# Expose the port number that Streamlit listens on
EXPOSE 8501

# Healthcheck to ensure the service is running
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run app.py when the container launches using conda run to ensure the environment is activated
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "gwas", "streamlit", "run", "home.py", "--server.port=8501"]
