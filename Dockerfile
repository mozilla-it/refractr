# FROM nginx:alpine #FIXME before production
FROM nginx

EXPOSE 80
EXPOSE 443

RUN mkdir /redirectr
WORKDIR /redirectr
COPY requirements.txt dodo.py bin /redirectr/
COPY etc/nginx/nginx.conf /etc/nginx/nginx.conf
COPY etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

#FIXME: before production
RUN apt-get update -y && apt-get install -y \
    vim

ENTRYPOINT /redirectr/bin/start.sh
