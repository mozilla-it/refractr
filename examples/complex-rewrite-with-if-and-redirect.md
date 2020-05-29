# Ex6 Complex: Rewrite with If and Redirect
file: [complex-rewrite-with-if-and-redirect](complex-rewrite-with-if-and-redirect.yml)
```
- dsts:
  - if <some-valid-nginx-predicate>
    ^: <rewrite>
  - redirect: (optional) <catchall-redirect> (used when the 'if' condtional fails)
  srcs: src(s)
```
```
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
The loaded data structure will be this:
```
- dsts:
  - ^: https://start.mozilla.org/$lang$request_uri
    if: $http_host ~ "^(?<lang>[a-z]{2,3}(-[a-z]{2})?)?\.(start.*)$"
  - redirect: https://start.mozilla.org/
  srcs:
  - '*.start.mozilla.com'
  - '*.start2.mozilla.com'
  - '*.start3.mozilla.com'
  - '*.start-prod.mozilla.com'
  status: 301
  tests:
  - http://ca.start.mozilla.com: https://start.mozilla.org/ca/
  - http://en-us.start.mozilla.com: https://start.mozilla.org/en-us/
  - http://en-uk.start.mozilla.com: https://start.mozilla.org/en-uk/
```
Note: In the complex(native) case the `srcs` and `dsts` keys match
exactly. As before, `status` will default to 301 if not specified.
However, the `tests` must be specified for rewrites such as this.
