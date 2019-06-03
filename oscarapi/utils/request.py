from django.urls import reverse


def get_domain(request):
    """
    Get the domain name parsed from a hostname:port string
    
    >>> get_domain("example.com:5984")
    "example.com"
    """
    return request.get_host().split(':')[0]


class IsApiRequest(object):
    @staticmethod
    def is_api_request(request):
        path = request.path.lower()
        api_root = reverse('api-root').lower()
        return path.startswith(api_root)
