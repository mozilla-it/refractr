# Simple: http->https

The example file: [simple-http-to-https.yml](simple-http-to-https.yml) has these sections.

## refracts

This is the simplest refract. A single domain is interpreted as
both the `srcs` and `dsts`.

## show

Because this is a scalar string value
and not a dictionary, the `status` defaults to `308` this is the
value that is given when the nginx ingress in refractr automatically
promotes all http->https.

## nginx

The nginx generated is just a simple server block with a redirect. This
block will never be hit because the nginx ingress is doing the redirect.

## validate

The validate step is standard just like other simple redirects.
