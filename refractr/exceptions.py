class URLError(Exception):
    def __init__(self, url):
        msg = f'error: with url={url}'
        super().__init__(msg)

class NonIfDstFoundError(Exception):
    def __init__(self, dst, status):
        msg = f'error: non-if dst found; dst={dst} status={status}'
        super().__init__(msg)

class LocationNotFoundInRewriteMatchError(Exception):
    def __init__(self, match):
        msg = f'error: location not found in rewrite match={match}'

class InsufficientAmountOfTestsError(Exception):
    def __init__(self, balance):
        msg = f'error: insufficent amount of tests; specify tests for rewrites; balance={balance}'
        super().__init__(msg)
