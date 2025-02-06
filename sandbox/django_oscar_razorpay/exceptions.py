class EmptyBasketException(Exception):
    pass


class MissingShippingAddressException(Exception):
    pass


class MissingShippingMethodException(Exception):
    pass


class InvalidBasket(Exception):
    """
    For when the user's basket can't be submitted (eg it has zero cost)

    The message of this exception is shown to the customer.
    """


class RazorpayError(Exception):
    pass
