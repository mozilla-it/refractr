# refractr

HTTP redirect and rewrite service based on nginx

## Links

* [SRE_INFO](docs/SRE_INFO.md)
* [Refractr Architecture](docs/refractr-architecture.md)

## refractr at mozilla

refractr runs on GKE at mozilla, app image is build with GitHub Actions, GKE resources are defined in a helm chart, app is deployed with Argo CD.

## refractr.yaml spec

This is the refractr (redirects|rewrites) spec file. Let's talk about the values that do not have to be specified and have sane defaults first:

### `dsts` key:

This is the destination that the redirect or rewrite will send the request. In most cases this is a single url. These never have `http(s)://` schemes. But in the more complicated redirects (Ex3) and rewrites (Ex4) it can have path logic or rewrite condtinals, respectively.

### `srcs` key:

This is the list of domains that requests will be redirected or rewritten from. These never have the `http(s)://` schemes. In the simple case (Ex1) they can be single scalar string value. But they can also be an array of strings as well (Ex2).

### `status` key:

One thing to remember for all refracts entries is that they default to: `status: 301` for doing redirects. Therefore, if not specified with `status` key, it will be 301. The `status` key can be added to any of the four examples: Ex1, Ex2, Ex3 or Ex4.

### `tests` key:

These are the `key: value` pairs that will be used during testing prior to deploy. They are written `src: dst`. The tests will be generated by default via product of dsts * srcs. If the `tests` key is specified, the autogenerate feature will be disabled in favor of the user-specified tests. The `tests` key can be added to any of the four examples: Ex1, Ex2, Ex3 or Ex4. In all instances, specifying the tests will override the default test generation behavior.

## Entries (refracts)

There are several ways to input a refracts. All entries will be preceeded with `-` because they are items in the `refractr` list (top level key).

### Simple:

Often the need is a simple redirect from one domain to another. A simple refract can be specified as single `key: value` pair item in the refracts list of items. The `key: value` pair in this case is: `destination: source(s)`. The destination is a single web url complete with the `https://` scheme. Note that `http://` are _not_ valid desitinations, whereas the source(s) can be a single source domain or list of multiples.

- [Ex1 Simple: Single Source](examples/simple-single-source.md)

spec:

```yaml
- destination(dsts): source(srcs)
```

example:

```yaml
- wiki.mozilla.org/: wiki.mozilla.com
```

- [Ex2 Simple: Multiple Sources](examples/simple-multiple-sources.md)

spec:

```yaml
- destination(dsts):
  - source1
  - source2
```

example:

```yaml
- www.mozillalabs.com/:
  - labs.mozilla.org
  - labs.mozilla.com
```

### Complex (native):

Sometimes the refract requires more control and input, especially when specifying a rewrite which requires this format. The handling of `status` and `tests` is exactly as above, but often you will want to specify the tests key: value `src: dst` pairs because rewrites can't deduce what would be good tests.

Sometimes for a redirect, you want to redirect paths on the domain to different destinations.  This is done via key: value `path: dst` under the `dsts` key. The sources will be the product of paths * srcs.

- [Ex3 Complex: Redirect, Paths -> Destinations](examples/complex-redirect.md)

spec:

```yaml
- dsts:
    path1: dst1
    path2: dst2
  srcs: src(s)
```

example:

```yaml
- dsts:
  - /faq.html: https://support.mozilla.org/products/firefox-lockwise/
  - /addon/updates.json: https://mozilla-lockwise.github.io/addon/updates.json
  - /: https://www.mozilla.org/firefox/lockwise/
  srcs: lockwise.firefox.com
```

Note: redirects (Ex4) and rewrites (Ex5) can and often are combined in a refract spec.

- [Ex4 Complex: Rewrite](examples/complex-rewrite.md)

spec:

```yaml
- dsts:
  - match1: dst1
  - match2: dst2
  srcs: src(s)
  tests:
    # must specify tests for each rewrite, because they won't be generated
  - src1: dst1
  - src2: dst2
```

example:

```yaml
 - dsts:
  - /tree.php/: people.mozilla.org/o
  - ^/search/(.*): 'people.mozilla.org/s?query=$1&who=staff'
  - /: people.mozilla.org/
  srcs: phonebook.mozilla.org
  status: 302
  tests:
    # this test must be specified because rewrites `^/(.*)` will not generate a test
  - http://phonebook.mozilla.org/search/test: https://people.mozilla.org/s?query=test&who=staff
```

Note: redirects (Ex4) and rewrites (Ex5) can and often are combined in a refract spec.

- [Ex5 Complex: Rewrite with If and Redirect Directives](examples/complex-with-if-and-redirect.md)

spec:

```yaml
- dsts:
  - if <some-valid-nginx-predicate>
    ^: <rewrite>
  - redirect: (optional) <catchall-redirect> (used when the 'if' condtional fails)
  srcs: src(s)
```

example:

```yaml
- dsts:
  - if: '$http_host ~ "^(?<lang>[a-z]{2,3}(-[a-z]{2})?)?\.(start.*)$"'
    ^: https://start.mozilla.org/$lang$request_uri
  - redirect: https://start.mozilla.org/
  srcs:
  - '*.start.mozilla.com'
  - '*.start2.mozilla.com'
  - '*.start3.mozilla.com'
  - '*.start-prod.mozilla.com'
  tests:
  - http://ca.start.mozilla.com: https://start.mozilla.org/ca/
  - http://en-us.start.mozilla.com: https://start.mozilla.org/en-us/
  - http://en-uk.start.mozilla.com: https://start.mozilla.org/en-uk/
```

- [Ex6 Raw Nginx](examples/raw-nginx.md)

spec:

```yaml
- nginx: |
    server {
        server_name name1 name2;

        etc
    }
  tests:
  - src: dst
```

example:

```yaml
- nginx: |
    server {
        server_name example.com;
        return 301 https://www.example.com;
    }
  tests:
  - http://example.com: https://www.example.com/
```
