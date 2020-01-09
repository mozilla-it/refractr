# FROM nginx:alpine #FIXME before production
FROM nginx

EXPOSE 80
EXPOSE 443

COPY etc/nginx/ /etc/nginx/

#FIXME: before production
RUN apt-get update -y && apt-get install -y \
    vim
