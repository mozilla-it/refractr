#!/bin/sh
SCRIPT=$(basename $0)
ACTION=$1
# Note: this is not bash, but sh instead
# POSIX "oneliner" to get script's directory
# https://stackoverflow.com/a/43919044
a="/$0"; a=${a%/*}; a=${a#/}; a=${a:-.}; DIR=$(cd "$a"; pwd)

usage() {
    cat <<EOF
usage: $SCRIPT [-h] {check,nginx,ingress,deployed,version,/bin/sh}

positional arguments:
  {check,nginx,ingress,deployed,version,/bin/sh}
                        choose action to run

optional arguments:
  -h, --help            show this help message and exit
EOF
}

hydrate() {
    if [ -z "$PAPERTRAIL_URL" ] && [ -z "$GCP_DEPLOY" ]; then
        echo "$SCRIPT ERROR: PAPERTRAIL_URL or GCP_DEPLOY env var must be set!"
        exit 1
    fi
    if [ -n "$PAPERTRAIL_URL" ]; then
      echo "hydrating AWS nginx.conf.template"
      envsubst '\$PAPERTRAIL_URL' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
    fi
    if [ -n "$GCP_DEPLOY" ]; then
      echo "hydrating GCP nginx.conf.template"
      # Cribbed from the nginx-unpriv container configuration
      # https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/mainline/debian/Dockerfile
      sed '/access_log/d' /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
      sed -i 's,pid /var/run/nginx.pid,pid /tmp/nginx.pid,' /etc/nginx/nginx.conf
      sed -i '/user nginx;/d' /etc/nginx/nginx.conf
      sed -i "/^http {/a \    proxy_temp_path /tmp/proxy_temp;\n    client_body_temp_path /tmp/client_temp;\n    fastcgi_temp_path /tmp/fastcgi_temp;\n    uwsgi_temp_path /tmp/uwsgi_temp;\n    scgi_temp_path /tmp/scgi_temp;\n" /etc/nginx/nginx.conf
      sed -i "s/80/8000/" /etc/nginx/conf.d/default.conf
    fi
}

case "$ACTION" in
    check)
        hydrate
        echo "check: nginx -t"
        exec nginx -t
        ;;
    nginx)
        hydrate
        echo "nginx: nginx -g daemon off;"
        exec nginx -g "daemon off;"
        ;;
    ingress)
        echo "ingress: kubectl apply -f $DIR/ingress.yaml"
        exec kubectl apply -f $DIR/ingress.yaml
        ;;
    deployed)
        echo "cat $DIR/deployed"
        cat $DIR/deployed
        ;;
    version)
        echo "cat $DIR/version"
        cat $DIR/version
        ;;
    /bin/sh)
        echo "/bin/sh"
        exec /bin/sh
        ;;
    *)
        usage
        exit 1
        ;;
esac

