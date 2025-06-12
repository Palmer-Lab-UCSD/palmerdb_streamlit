### Build Stage
# Install Poetry
FROM python:3.11-slim as builder
WORKDIR /app

RUN apt-get update \
    && apt-get install -y \
         curl \
	git \
         build-essential \
         libffi-dev \
         libpq-dev \
         python3-dev \
         openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH=/root/.local/bin:${PATH}

RUN python -m venv ./venv

COPY pyproject.toml poetry.lock ./

RUN . /app/venv/bin/activate && poetry install

### Prod Stage
# Get venv
FROM python:3.11-slim as prod
WORKDIR /app
COPY --from=builder /app/venv /app/venv

ENV PATH=/app/venv/bin:${PATH}

# Copy all files from the current directory to the working directory
COPY . . 

# organize
COPY auth.env secrets.toml ./.streamlit/
 
# Expose the port number that Streamlit listens on
EXPOSE 8501

# Run app.py when the container launches using conda run to ensure the environment is activated
ENTRYPOINT ["/app/venv/bin/python", "-m", "streamlit", "run", "home.py", "--server.port=8501"]