# Ex3 Simple: Multiple Sources

Here is the use case when you need to supply more than one source domain.

The example file: [simple-multiple-sources.yml](simple-multiple-sources.yml) has these sections.

## refracts

This is the example specification of a refract in this way. The dst in on
the left and always ends with a trailing `/` and never has a scheme specified
like `http://` or `https://`. In this case the srcs are a list of domains
that will all redirect to this desintation the same.

## show

This section shows what the refract looks like after it has been loaded and
normalized to the these data fields. If unspecified status will default to
`301`. Any tests specified will be added to the generated tests. The number
of tests generated is always the product of srcs x dsts.

## nginx

This shows the nginx that will be generated for this refract.

## validate

This is the output of the validate step done against a localhost running
container. Each test loaded will be used in this step. The destination and
status will be compared against the expected destination and status.
