# Ex2 Simple: Single Source

Here any requests that go to wiki.mozilla.com will be redirected to
https://wiki.mozilla.org.

The example file: [simple-single-source.yml](simple-single-source.yml) has these sections.

## refracts

This is the example specification of a refract in this way. The dst in on
the left and always ends with a trailing `/` and never has a scheme specified
like `http://` or `https://`.

## show

This section shows what the refract looks like after it has been loaded and
normalized to the these data fields. If unspecified status will default to
`301`. Any tests specified will be added to the generated tests.

## nginx

This shows the nginx that will be generated for this refract.

## validate

This is the output of the validate step done against a localhost running
container. Each test loaded will be used in this step. The destination and
status will be compared against the expected destination and status.
