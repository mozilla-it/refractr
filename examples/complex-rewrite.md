# Ex4 Complex: Rewrite

The example file: [complex-rewrite.yml](complex-rewrite.yml) has these sections.

## refracts

These are more complicated refracts when you need to specify different
matches to rewrite the url to different destinations. Under the `dsts` field
each path must start with a `^/` followed by a match with a capture to
rewrite as the key. The value is the desired destination for the rewrite with
the capture value like `$1`.

## show

This section shows what the refract looks like after it has been loaded and
normalized to the these data fields. If unspecified, status will default to
`301`. However, on a rewrite `301` becomes `permanent` and `302` becomes
`redirect` on the rewrite statement in nginx. Any tests specified will be
added to the generated tests. Tests will *not* be generated for any rewrites.

## nginx

This shows the nginx that will be generated for this refract. Notice that
each rewrite is protected by a location block for the path portion of the
rewrite match. These location blocks *do not* have the `=` prefix which
means that they are prefix matches only in nginx's spec.

## validate

This is the output of the validate step done against a localhost running
container. Each test loaded will be used in this step. The destination and
status will be compared against the expected destination and status.

Note: remember the status and tests are defaults if unspecified. Here you
can see how the tests specify `src: dst` incorporating the path fragments.
