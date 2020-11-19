import doctest

import oscarapi.serializers.utils
import oscarapi.utils.request
import oscarapi.utils.files
import oscarapi.utils.url


def load_tests(loader, tests, ignore):  # pylint: disable=W0613
    tests.addTests(
        [
            doctest.DocTestSuite(oscarapi.serializers.utils),
            doctest.DocTestSuite(oscarapi.utils.request),
            doctest.DocTestSuite(oscarapi.utils.files),
            doctest.DocTestSuite(oscarapi.utils.accessors),
            doctest.DocTestSuite(oscarapi.utils.url),
        ]
    )
    return tests
