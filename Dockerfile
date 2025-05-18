# Dockerfile using pip instead of Poetry

 

# Base image

FROM python:3.12.6-bullseye

 

# Set environment variables

ENV PYTHONUNBUFFERED=1 \

    PYTHONDONTWRITEBYTECODE=1 \

    PIP_NO_CACHE_DIR=off \

    PIP_DISABLE_PIP_VERSION_CHECK=on \

    PIP_DEFAULT_TIMEOUT=100

 

# Install dependencies

RUN apt-get update \

    && apt-get install --no-install-recommends -y curl \

    && rm -rf /var/lib/apt/lists/*

 

# Set working directory

WORKDIR /app

 

# Copy only requirements to leverage Docker layer caching

COPY requirements.txt .

 

# Install Python dependencies

RUN pip install --upgrade pip \

    && pip install -r requirements.txt

 

# Copy the rest of the application code

COPY . .

 

# Optional: Install python-dotenv if not already in requirements.txt

RUN pip install python-dotenv

 

# Expose application port

EXPOSE 8000

 

# Command to run the application

CMD ["python", "main.py"]