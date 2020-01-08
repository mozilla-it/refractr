#!/bin/bash

# Generate our nginx config
cd /redirectr
./bin/refractr > /etc/nginx/conf.d/refractr.conf

# Run nginx in the foreground
nginx -g 'daemon off;'
