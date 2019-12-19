FROM python:3.8.0-slim-buster as web

WORKDIR /app
EXPOSE 80

ENV PATH="/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Setup OS
#RUN pip install --upgrade pip
#RUN pip install virtualenv
#RUN python3 -m virtualenv venv
# Comnbine apt-get update and apt-get install in a single RUN command to avoid Docker caching issues
RUN apt-get update -y && apt-get install -y \
    curl \
    nginx \
    procps \
    python-pip 

# Setup app
COPY /app /app
RUN pip install --no-cache-dir -r /app/requirements.txt 
ARG GIT_SHA=head
ENV GIT_SHA=${GIT_SHA}
# Generate nginx config here

# Run tests here


# Run nginx in the foreground
CMD nginx -g 'daemon off;'
