# SRE Info

This is the SRE_INFO.md file which should be found in the root of any source code that is administered by the Mozilla SRE Green team. We are available on #sre on slack.

## Overview

refractr, the application, involves the following parts:

- refractr DSL, schema & python code to validate & translate YAML to nginx configurations.
- doit DSL (dodo.py) to run meta-tasks for this pipeline as part of CI / CD.
- docker / docker compose, to serve refracts via a modified nginx image.

## Doit (dodo.py)

Doit is a Python framework meant to replace Makefiles and similar tools. The following are the Doit tasks we have defined and run as part of CI for Refractr:

```sh
build                       run docker compose build for refractr
certificate_manager_input   create input file for certificate manager tf module
check                       run nginx -t test on refractr nginx config
deployed                    write refractr/deployed json file
drun                        run refractr container via docker compose up -d
ingress                     create ingress.yaml from refractr.yml domains and ingress.yaml.template
nginx                       generate nginx.conf files from refractr.yml
publish                     publish docker image to aws ECR
refracts                    create refracts.json from loading refractr.yml
refractslisting             create refracts list  from loading refractr.json
schema                      test refractr.yml against schema.yml using jsonschema
show                        show CI variables
test                        run pytest tests against the locally running container
version                     write refractr/version json file
```

## infra

refractr is deployed to GKE as a GCPv2 tenant. Part of the infra is a Gateway API based Loadbalancer, SSL certificates are generated via terraform, using Google's Certificate Manager. The Loadbalancer references the certificates with the `networking.gke.io/certmap` annotation.

## determining app health

* stage
    * `curl -sSL stage.refractr.nonprod.webservices.mozgcp.net/version |jq`
    * `curl -sSL stage.refractr.nonprod.webservices.mozgcp.net/deployed |jq`

* prod
    * `curl -sSL prod.refractr.prod.webservices.mozgcp.net/version |jq`
    * `curl -sSL prod.refractr.prod.webservices.mozgcp.net/deployed |jq`
