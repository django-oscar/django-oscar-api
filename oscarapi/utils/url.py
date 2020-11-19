from urllib.parse import quote, urlparse, urlunparse


def cleanup_url(url):
    """
    cleanup url so urlretrive does not throw a InvalidURL exception
    
    >>> cleanup_url("http://example.com/I am an image.jpg")
    'http://example.com/I%20am%20an%20image.jpg'
    """
    parse_result = urlparse(url)
    return urlunparse((
        parse_result.scheme,
        parse_result.netloc,
        quote(parse_result.path),
        parse_result.params,
        parse_result.query,
        parse_result.fragment,
    ))
