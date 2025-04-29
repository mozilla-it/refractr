# SRE Info

This is the SRE_INFO.md file which should be found in the root of any source code that is administered by the Mozilla SRE Green team. We are available on #sre on slack.

## Overview

refractr consists of the following parts:

- refractr DSL & schema
- python code & dependency management
- docker / docker-compose files

### refractr DSL & schema

refractr is a mozcloud tenant, runs on GKE, is build with GitHub actions and deployed with Argo CD. The application image is based on the offficial upstream nginx image, the only difference is that it actually bundles an auto-generated config file that handles all of mozilla's redirect requirements.

refractr itself is actually the python code that generates the nginx config based on the DSL & schema in this repository.

### python code & dependency management

refractr is written in python, dependencies are managed with [poetry](https://python-poetry.org/). To simplify interacting with the app, a task-runner has been added ([pydoit](https://pydoit.org)). Tasks are used in CI, `show`, `check` and `test` are pretty useful when working with the code / refract definitions, too.


```sh
$ poetry run doit list
build                       run docker compose build for refractr
certificate_manager_input   create input file for certificate manager tf module
check                       run nginx -t test on refractr nginx config
deployed                    write refractr/deployed json file
drun                        run refractr container via docker compose up -d
nginx                       generate nginx.conf files from refractr.yml
refracts                    create refracts.json from loading refractr.yml
refractslisting             create refracts list  from loading refractr.json
schema                      test refractr.yml against schema.yml using jsonschema
show                        show CI variables
test                        run pytest tests against the locally running container
version                     write refractr/version json file
```

### common tasks

#### update refracts

The main thing refractr does is read in `yaml` files that define actual redirects, e.g. `smartdogz.org` >> `https://www.mozilla.org/` and translate them into an nginx config file. The repo contains contains a `stage-refractr.yml` and a `prod-refractr.yml` file, these are of interest for refractr's stage & prod environments and define all the redirects the system handles.

When an update to e.g. `prod-refractr.yaml` was made, you can validate the system functionality with the `check` and `test` targets. The `check` target basically does the translation, a `$ docker-compose build`, and a final call to `nginx -t` in the built container. If this task doesn't return any errors, you can be sure that the input files still produce a use-able nginx config file. Next step is usually `test`, which takes the built container and runs unittests against each individual refract. If this command didn't return errors either, you've made a successful refractr update.

#### deployment

We automatically deploy a stage & prod env for refractr. Stage is deployed whenever a merge to `main` is done, prod is deployed when a GitHub release is created (or a tag has been pushed), that matches the pattern `v\d+\.\d+\.\d+`. In both cases, GitHub actions will build the docker image, Argo CD will ship it to GKE.

#### update certificates

Refractr's Loadbalancer is build from Gateway API resources by GCP's Gateway API Controller. The system handles ~180 redirects and forces TLS for every refract, which results in ~360 SSL certificates attached to the Loadbalancer. To be able to make use of such a high number of SSL certificates at once, we're using GCP's certificate manager API to map hostnames to certificates. Certificate manager API defines a certmap (that is attached to the Gateway API Loadbalancer via an annotation), which in turn defines entries that map hostnames to certificates.

Certificates and certificate-map-entries are managed with terraform, because no method for building them alongside the Gateway API resources directly from GKE was available at the time of migrating to mozcloud.

To simplify this, we're using a [terraform-module](https://github.com/mozilla/terraform-modules/tree/main/google_certificate_manager_certificate_map), which reads all refract definitions in from a single yaml document. This document can be generated with a `doit` task, `$ poetry run doit certificate_manager_input`. Once generated and put in place, refractr's certmap can be updated with a PR in to the infra repo.

#### DNS

For refractr to actually redirect something, sources must be pointed at the application Loadbalancer in DNS. Usually, this is done with a CNAME, for some scenarios, it might be necessary to point to the Loadbalancer's actual IP address with an A and / or AAAA record. Of course, this is also a requirement for certificate manager API to be able to validate SSL cert requests. If an individual refract's uptime is critical, you probably want to generate an intermediate cert before doing a DNS switch and add it to refractr's certmap with `gcloud` first.

#### app health

Refractr provides a couple of useful endpoints for troubleshooting:

```shell
# check the currently deployed app version
$ curl -sSL stage.refractr.nonprod.webservices.mozgcp.net/version |jq
{
  "BRANCH": "main",
  "REVISION": "ab313c2bce655fec1a4ad0d377aa671da1c2839e",
  "VERSION": "v0.0.209-2-gab313c2"
}

# check known refracts
$ curl -sSL stage.refractr.nonprod.webservices.mozgcp.net/refracts |jq
{
  "refracts": [
    {
      "dsts": [
        "mozilla.org/"
      ],
      "srcs": [
        "refractr.allizom.org"
      ],
      "status": 301,
      "headers": {
        "Strict-Transport-Security": "\"max-age=60; includeSubDomains\" always"
      },
      "hsts_img": false,
      "preserve_path": true,
      "wildcard_file": null,
      "tests": [
        {
          "http://refractr.allizom.org": "https://mozilla.org/"
        },
        {
          "http://refractr.allizom.org/path": "https://mozilla.org/path"
        }
      ]
    },
    {
      "dsts": [
        "mozilla.com/"
      ],
      "srcs": [
        "refractr1.allizom.org"
      ],
      "status": 301,
      "headers": {
        "Strict-Transport-Security": "\"max-age=60; includeSubDomains\" always"
      },
      "hsts_img": false,
      "preserve_path": true,
      "wildcard_file": null,
      "tests": [
        {
          "http://refractr1.allizom.org": "https://mozilla.com/"
        },
        {
          "http://refractr1.allizom.org/path": "https://mozilla.com/path"
        }
      ]
    }
  ],
  "refracts-count": 2
}
```
