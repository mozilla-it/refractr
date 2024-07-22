class URLError(Exception):
    def __init__(self, url):
        msg = f"error: with url={url}"
        super().__init__(msg)


class NonIfDstsFoundError(Exception):
    def __init__(self, dsts, status):
        msg = f"error: non-if dsts found; dsts={dsts} status={status}"
        super().__init__(msg)


class LocationNotFoundInRewriteMatchError(Exception):
    def __init__(self, match):
        msg = f"error: location not found in rewrite match={match}"


class InsufficientAmountOfTestsError(Exception):
    def __init__(self, balance):
        msg = f"error: insufficent amount of tests; specify tests for rewrites; balance={balance}"
        super().__init__(msg)
