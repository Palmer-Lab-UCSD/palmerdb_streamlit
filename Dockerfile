### Build Stage
# Use Miniconda as a base image
FROM continuumio/miniconda3 AS builder

# Update conda and add the conda-forge channel
RUN conda update -n base -c defaults conda && \
    conda install -c conda-forge conda-pack && \
    conda config --add channels conda-forge && \
    conda config --add channels bioconda

# copy env files
COPY gwas.yml lzenv.yml .

# Create the envs
RUN conda env create -f gwas.yml
RUN conda env create -f lzenv.yml

# Use conda-pack to create a standalone environment
RUN conda-pack -n gwas -o /tmp/gwas.tar -f --ignore-missing-files --exclude lib/python3.1 && \
    mkdir -p /venv/gwas && \
    tar xf /tmp/gwas.tar -C /venv/gwas && \
    rm /tmp/gwas.tar && \
    conda-pack -n lzenv -o /tmp/lzenv.tar -f --ignore-missing-files --exclude lib/python3.1 && \
    mkdir -p /venv/lzenv && \
    tar xf /tmp/lzenv.tar -C /venv/lzenv && \
    rm /tmp/lzenv.tar && \
    /venv/gwas/bin/conda-unpack && \
    /venv/lzenv/bin/conda-unpack

### Final Image

FROM debian:bookworm-slim AS streamlit

# envs
COPY --from=builder /venv /venv

# dependencies
RUN apt-get update && apt-get install -y \
    curl \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# set path
ENV PATH=/venv/gwas/bin:${PATH}

# set directory
WORKDIR /app 

# Copy all files from the current directory to the working directory
COPY . . 

# organize
COPY gwas_class_auto.py ./GWAS_pipeline/
COPY auth.env secrets.toml ./.streamlit/
COPY m2zfast.conf ./GWAS_pipeline/locuszoom/conf/
COPY rn7.db ./GWAS_pipeline/databases/
 
# Expose the port number that Streamlit listens on
EXPOSE 8501

# Run app.py when the container launches using conda run to ensure the environment is activated
ENTRYPOINT ["/venv/gwas/bin/python", "-m", "streamlit", "run", "home.py", "--server.port=8501"]