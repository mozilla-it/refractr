FROM nginx:1.26.1

ARG UID=10001
ARG GID=10001

RUN groupadd -g ${GID} app; \
  useradd -g ${GID} -u ${UID} -s /usr/sbin/nologin -m app; \
  chown -R app:app /etc/nginx/

COPY nginx/nginx.conf.template /etc/nginx/nginx.conf
COPY nginx/conf.d/ /etc/nginx/conf.d/
COPY image/ /refractr/

USER app

EXPOSE 8000

ENTRYPOINT ["/refractr/refractr.sh"]
CMD ["nginx"]
