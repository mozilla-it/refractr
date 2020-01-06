# FROM nginx:alpine #FIXME before production
FROM nginx

EXPOSE 80
EXPOSE 443

COPY etc/nginx/nginx.conf /etc/nginx/nginx.conf
COPY etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
COPY etc/nginx/conf.d/refractr.conf /etc/nginx/conf.d/refractr.conf

#FIXME: before production
RUN apt-get update -y && apt-get install -y \
    vim
