# nginx:alpine contains NGINX_VERSION environment variable, like so:
ARG NGINX_VERSION=1.17.6

FROM nginx:alpine AS builder

# Download sources
RUN wget "http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz"

# For latest build deps, see https://github.com/nginxinc/docker-nginx/blob/master/mainline/alpine/Dockerfile
RUN apk add --no-cache --virtual .build-deps \
  gcc \
  libc-dev \
  make \
  openssl-dev \
  pcre-dev \
  zlib-dev \
  linux-headers \
  curl \
  gnupg \
  libxslt-dev \
  gd-dev \
  geoip-dev \
  git

# FIXME: this is not pinning a version; it's the tip of master
RUN git clone http://github.com/influxdata/nginx-influxdb-module.git

# Reuse same cli arguments as the nginx:alpine image used to build
RUN CONFARGS=$(nginx -V 2>&1 | sed -n -e 's/^.*arguments: //p') \
  tar -zxC . -f nginx-${NGINX_VERSION}.tar.gz && \
  MODULEDIR="$(pwd)/nginx-influxdb-module" && \
  cd nginx-${NGINX_VERSION} && \
  ./configure --with-compat $CONFARGS --add-dynamic-module=$MODULEDIR && \
  make && make install

FROM nginx:${NGINX_VERSION}-alpine
# Extract the dynamic module influxdb from the builder image
COPY --from=builder /usr/local/nginx/modules/ngx_http_influxdb_module.so /usr/local/nginx/modules/ngx_http_influxdb_module.so
RUN rm /etc/nginx/conf.d/default.conf

COPY nginx/ /etc/nginx/
EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["nginx", "-g", "daemon off;"]
