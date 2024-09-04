#!/bin/sh

SCRIPT=$(basename $0)
ACTION=$1

a="/$0"; a=${a%/*}; a=${a#/}; a=${a:-.}; DIR=$(cd "$a"; pwd)

usage() {
    cat <<EOF
usage: $SCRIPT [-h] {check,nginx,deployed,version,/bin/sh}

positional arguments:
  {check,nginx,deployed,version,/bin/sh}
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

