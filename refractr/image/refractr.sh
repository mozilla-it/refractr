#!/bin/sh

ACTION=$1
# Note: this is not bash, but sh instead
# POSIX "oneliner" to get script's directory
# https://stackoverflow.com/a/43919044
a="/$0"; a=${a%/*}; a=${a#/}; a=${a:-.}; DIR=$(cd "$a"; pwd)

usage() {
    cat <<EOF
usage: $(basename $0) [-h] {check,nginx,ingress,deployed,version,/bin/sh}

positional arguments:
  {check,nginx,ingress,deployed,version,/bin/sh}
                        choose action to run

optional arguments:
  -h, --help            show this help message and exit
EOF
}

case "$ACTION" in
    check)
        echo "check: nginx -t"
        exec nginx -t
        ;;
    nginx)
        echo "nginx: nginx -g daemon off;"
        exec nginx -g "daemon off;"
        ;;
    nginx-logs)
        echo "nginx: nginx -g daemon off; 2>&1 | tee /logs/nginx.log"
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

