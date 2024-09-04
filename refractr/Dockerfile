FROM nginx:1.26.2

COPY --chown=nginx:nginx nginx/nginx.conf.template /etc/nginx/nginx.conf
COPY --chown=nginx:nginx nginx/conf.d/default.conf nginx/conf.d/refractr.conf /etc/nginx/conf.d/
COPY --chown=nginx:nginx image/deployed image/version image/refractr.sh image/refracts /refractr/

EXPOSE 8000

USER nginx

ENTRYPOINT ["/refractr/refractr.sh"]
CMD ["nginx"]
