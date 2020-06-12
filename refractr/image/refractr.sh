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
    if [ -z "$PAPERTRAIL_URL" ]; then
        echo "$SCRIPT ERROR: PAPERTRAIL_URL env var must be set!"
        exit 1
    fi
    echo "hydrating nginx.conf.template"
    envsubst '\$PAPERTRAIL_URL' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
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

