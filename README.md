# refractr [![Build Status](https://travis-ci.com/mozilla-it/refractr.svg?branch=master)](https://travis-ci.com/mozilla-it/refractr)
yaml -> nginx for redirects and rewrites

# Installing refractr in Kubernetes

## First install cert-manager if not already installed:

### Add the cert-manager CRD
```
kubectl apply --validate=false \
    -f https://raw.githubusercontent.com/jetstack/cert-manager/release-0.13/deploy/manifests/00-crds.yaml
```

### Add the Jetstack Helm repository
```
helm repo add jetstack https://charts.jetstack.io
```

### Install the cert-manager helm chart
```
helm install --name my-release --namespace cert-manager jetstack/cert-manager
```

## Install refractr RBAC and nginx ingress

```
# Currently this has the refractr-stage namespace hardcoded in two places, adjust as necessary
kubectl apply -f k8s/namespace.yaml -f k8s/serviceaccount.yaml -f k8s/nginx/
```

## Install the refractr helm chart
```
$ helm install --name refractr --set issuer=<issuer> --namespace mynamespace refractr
```
where issuer is one of stage or prod to pick which Let's Encrypt server to use.  For example:
```
$ helm install --name refractr --set issuer=prod --namespace refractr-prod refractr
```
