# Ex7 Raw Nginx

The example file: [raw-nginx.yml](raw-nginx.yml) has these sections.

## refract

You can specify raw nginx which will be a straight passthrough.
Note: tests will not be generated so they must be specified.

## show

The refract doesn't have `dsts`, `srcs` or `status` as the raw nginx is specified
instead. However it is important to specify all the tests necessary to
validate the nginx.

## nginx

As stated befor the nginx is a straight passthrough from the `nginx` field
in the refract.

## validate

The validate action will run all the tests against the raw nginx specified.
The tests must spupply a status value to expect since `status` field was not
specified in this case.
