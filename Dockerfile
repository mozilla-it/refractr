FROM nginx

WORKDIR /app
EXPOSE 80

ENV PATH="/venv/bin:$PATH" \
    GIT_SHA=${GIT_SHA}

# Setup OS
#RUN pip install --upgrade pip
#RUN pip install virtualenv
#RUN python3 -m virtualenv venv
# Comnbine apt-get update and apt-get install in a single RUN command to avoid Docker caching issues
RUN apt-get update -y && apt-get install -y \
    curl \
    nginx \
    procps

# Setup app
COPY /nginx.conf /etc/nginx/conf/default.conf
ARG GIT_SHA=head
# Generate nginx config here

# Run tests here

