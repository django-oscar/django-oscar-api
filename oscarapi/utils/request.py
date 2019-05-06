def get_domain(request):
    """
    Get the domain name parsed from a hostname:port string
    
    >>> get_domain("example.com:5984")
    "example.com"
    """
    return request.get_host().split(':')[0]

