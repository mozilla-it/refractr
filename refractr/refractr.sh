#!/bin/sh

ACTION=$1

usage() {
    cat <<EOF
usage: $(basename $0) [-h] {check,nginx,ingress,/bin/sh}

positional arguments:
  {check,nginx,ingress,/bin/sh}
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
    ingress)
        echo "ingress: kubectl apply -f /etc/ingress.yaml"
        exec kubectl apply -f /etc/ingress.yaml
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

