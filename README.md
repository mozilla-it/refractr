# refractr [![Build Status](https://travis-ci.com/mozilla-it/refractr.svg?branch=master)](https://travis-ci.com/mozilla-it/refractr)
yaml -> nginx for redirects and rewrites

[![Build Status](https://travis-ci.com/mozilla-it/refractr.svg?branch=master)](https://travis-ci.com/mozilla-it/refractr)

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

### Create namespace and RBAC


