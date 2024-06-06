# nginx:alpine contains NGINX_VERSION environment variable, like so:
ARG NGINX_VERSION=1.21.6
ARG KUBECTL_VERSION=v1.15.11

FROM nginx:${NGINX_VERSION}-alpine AS builder
LABEL stage=intermediate

# required after the FROM statement to pass through
ARG NGINX_VERSION
ARG KUBECTL_VERSION

# grab binary from github releases
RUN wget https://storage.googleapis.com/kubernetes-release/release/$KUBECTL_VERSION/bin/linux/amd64/kubectl

# mark as executable
RUN chmod +x ./kubectl

FROM nginx:${NGINX_VERSION}-alpine

# Extract the kubectl from the builder image
COPY --from=builder ./kubectl /usr/local/bin/kubectl

RUN rm /etc/nginx/conf.d/default.conf
COPY image/ /refractr
COPY nginx/ /etc/nginx/

RUN chown -R nginx:nginx /etc/nginx

EXPOSE 80
STOPSIGNAL SIGTERM

ENTRYPOINT ["/refractr/refractr.sh"]
CMD ["nginx"]
