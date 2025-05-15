# backend/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2 (PostgreSQL adapter)
# and other potential native extensions.
# Using --no-install-recommends reduces image size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache, which can reduce image size.
# -r requirements.txt: Installs packages from the given requirements file.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
COPY . /app/

# Command to run the Uvicorn server when the container launches
# Uvicorn is an ASGI server, suitable for FastAPI.
# --host 0.0.0.0: Makes the server accessible externally (from other containers and the host).
# --port 8000: Specifies the port the server will listen on.
# main:app: Tells Uvicorn to find the FastAPI application instance named 'app' in the 'main.py' file.
# --reload: Enables auto-reloading for development (remove for production).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
