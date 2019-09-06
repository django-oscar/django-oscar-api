from rest_framework.fields import empty


def destructure(dictionary, *keys):
    """
    Select sub-dictionary

    >>> d = {"henk": 1, "klaas": 2, "hent": 7}
    >>> destructure(d, "klaas")
    {'klaas': 2}
    >>> sorted(destructure(d, "henk", "hent").items())
    [('henk', 1), ('hent', 7)]
    >>> destructure(d, "henk", "kak")
    {'henk': 1}
    """
    return dict(_getitems(dictionary, *keys))


def _getitems(dictionary, *keys):
    """
    Get existing items of a dict lazy

    >>> d = {"henk": 1, "klaas": 2, "hent": 7}
    >>> r = _getitems(d, "klaas")
    >>> list(r)
    [('klaas', 2)]
    >>> r = _getitems(d, "henk", "hent")
    >>> list(r)
    [('henk', 1), ('hent', 7)]
    >>> r = _getitems(d, "henk", "kak")
    >>> list(r)
    [('henk', 1)]
    """
    for key in keys:
        result = dictionary.get(key, empty)
        if result is empty:
            continue
        yield (key, result)


def getitems(dictionary, *keys):
    """
    Get existing items of a dict lazy

    >>> d = {"henk": 1, "klaas": 2, "hent": 7}
    >>> r = getitems(d, "klaas")
    >>> list(r)
    [2]
    >>> r = getitems(d, "henk", "hent")
    >>> list(r)
    [1, 7]
    >>> r = getitems(d, "henk", "kak")
    >>> list(r)
    [1, None]
    """
    for key in keys:
        yield dictionary.get(key)


def select(obj, *attrs):
    """
    Select attributes of object

    >>> from argparse import Namespace
    >>> d = Namespace(henk=1, klaas=2, hent=7)
    >>> select(d, "klaas")
    {'klaas': 2}
    >>> sorted(select(d, "henk", "hent").items())
    [('henk', 1), ('hent', 7)]
    >>> select(d, "henk", "kak")
    {'henk': 1}
    """
    return dict(_getattrs(obj, *attrs))


def _getattrs(obj, *attrs):
    """
    Get existing attributes of an object lazy

    >>> from argparse import Namespace
    >>> d = Namespace(henk=1, klaas=2, hent=7)
    >>> r = _getattrs(d, "klaas")
    >>> list(r)
    [('klaas', 2)]
    >>> r = _getattrs(d, "henk", "hent")
    >>> list(r)
    [('henk', 1), ('hent', 7)]
    >>> r = _getattrs(d, "henk", "kak")
    >>> list(r)
    [('henk', 1)]
    """
    for attr in attrs:
        result = getattr(obj, attr, empty)
        if result is empty:
            continue
        yield (attr, result)


def getattrs(obj, *attrs):
    """
    Get existing attributes of an object lazy

    >>> from argparse import Namespace
    >>> d = Namespace(henk=1, klaas=2, hent=7)
    >>> r = getattrs(d, "klaas")
    >>> list(r)
    [2]
    >>> r = getattrs(d, "henk", "hent")
    >>> list(r)
    [1, 7]
    >>> r = getattrs(d, "henk", "kak")
    >>> list(r)
    [1, None]
    """
    for attr in attrs:
        yield getattr(obj, attr, None)
